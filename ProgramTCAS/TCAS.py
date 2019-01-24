import pygame as pg
from pygame import font
from pygame import draw as pgD
from math import pi, sqrt, sin, cos, atan2


##  Definition of some constant values
WIDTH = 910
HEIGHT = 750
SAMPLING_TIME = 8
BACKGROUNG_COLOR = [4, 4, 4]
WHITE = [255, 255, 255]
BLACK = [0, 0, 0]
GREEN = [0, 255, 0]
BLUE = [135, 206, 250]
ORANGE = [255, 165, 0]
YELLOW = [255, 255, 0]
RED = [255,0,0]
GREY = [150, 150, 150]
NM2m = 1852
ft2m = 0.3048
AP_POS = 5 / 6 * HEIGHT * 0.9
D1 = int(1 / 6 * HEIGHT * 2)
D2 = int(2 / 6 * HEIGHT * 2)
D3 = int(3 / 6 * HEIGHT * 2)
D4 = int(4 / 6 * HEIGHT * 2)
MY_ID = 100
RANGE = 20


class Airplane:
    """docstring for Airplane - This class defines an airplane object, based
    on its position, id, TCAS status and vertical velocity"""
    ##  tcas_status:
    #   0-> nothing
    #   1-> other aircraft
    #   2-> proximate aircraft
    #   3-> TA
    #   4-> RA

    coord_geo = {}
    coord_ecef = {}
    coord_enu = {}
    coord_disp = {}
    coord_real = {}
    status = 0
    tcas_status = 0
    dist = 0
    relative_alt = 0
    v_z = 0
    checkmove = 0
    id = 0

    def __init__(self, coord_geo):
        self.coord_geo = coord_geo
        self.update_coord_ecef(coord_geo)

    def update_coord_geo(self, new_coord_geo):
        lat = new_coord_geo['Latitude']
        long = new_coord_geo['Longitude']
        alt = new_coord_geo['Altitude']
        self.coord_geo = {'Latitude': lat, 'Longitude': long, 'Altitude': alt}

    def update_coord_ecef(self, coord_g):
        #according to WGS84
        a = 6378137.0  # meters
        f = 1/298.257223563
        aux = 1-f*(2-f)*sin(coord_g['Latitude'])*sin(coord_g['Latitude'])
        N = a/(sqrt(aux))
        x = (N + coord_g['Altitude'])
        x = x*cos(coord_g['Latitude'])*cos(coord_g['Longitude'])
        y = (N + coord_g['Altitude'])
        y = y*cos(coord_g['Latitude'])*sin(coord_g['Longitude'])
        z = ((1-f)*(1-f)*N + coord_g['Altitude']) * sin(coord_g['Latitude'])
        self.coord_ecef = {'x': x, 'y': y, 'z': z}

    def update_coord_enu(self, coord_geo, coord_ecef):
        c = self.coord_ecef
        lat = 'Latitude'
        lon = 'Longitude'
        x = -sin(coord_geo[lon])*(c['x']-coord_ecef['x'])
        x = x+cos(coord_geo[lon])*(c['y']-coord_ecef['y'])
        y = -sin(coord_geo[lat])*cos(coord_geo[lon])
        y = y*(c['x']-coord_ecef['x'])
        y = y-sin(coord_geo[lat])*sin(coord_geo[lon])*(c['y']-coord_ecef['y'])
        y = y+cos(coord_geo[lat])*(c['z']-coord_ecef['z'])
        z = cos(coord_geo[lat])*cos(coord_geo[lon])
        z = z*(c['x']-coord_ecef['x'])
        z = z+cos(coord_geo[lat])*sin(coord_geo[lon])*(c['y']-coord_ecef['y'])
        z = z+sin(coord_geo[lat])*(c['z']-coord_ecef['z'])
        self.coord_enu = {'x': x, 'y': y, 'z': z}

    def update_display_coord(self, ref_head):
        x_ = cos(ref_head)*self.coord_enu['x']-sin(ref_head)*self.coord_enu['y']
        y_ = sin(ref_head)*self.coord_enu['x']+cos(ref_head)*self.coord_enu['y']
        self.coord_real = {'x': x_, 'y': y_, 'z': self.coord_enu['z']}
        self.dist = sqrt(x_ * x_ + y_ * y_)
        self.relative_alt = self.coord_enu['z']
        theta = atan2(y_, x_)
        r = D4*sqrt(x_*x_+y_*y_)/(20*NM2m)/2
        x_disp = r*cos(theta)
        y_disp = -r*sin(theta)
        dict = {}
        dict['x'] = x_disp + WIDTH/2
        dict['y'] = y_disp + AP_POS
        dict['z'] = self.coord_enu['z']
        self.coord_disp = dict

    def update_coord(self, new_coord_geo, ref_heading, coord_geo_radar={},
    coord_ecef_radar={}, own=False):
        self.update_coord_geo(new_coord_geo)
        self.update_coord_ecef(self.coord_geo.copy())
        if own is False:
            self.update_coord_enu(coord_geo_radar, coord_ecef_radar)
            self.update_display_coord(ref_heading)
        else:
            self.update_coord_enu(self.coord_geo.copy(), self.coord_ecef.copy())
            self.update_display_coord(ref_heading)
        return


class TCAS:

    def __init__(self):
        self.Our_Airplane = self.__make_airplane__(0, 0, 0, 0, MY_ID, own=True)
        self.Other_Airplanes = []
        pg.init()
        font.init()
        self.gD = pg.display.set_mode((WIDTH, int(HEIGHT*0.9)))
        pg.display.set_caption('Simulation')
        self.clock = pg.time.Clock()
        self.gD.fill(BACKGROUNG_COLOR)
        pg.display.update()
        self.clock.tick(SAMPLING_TIME)
        self.gameExit = False
        return

    def quit(self):
        pg.quit()

    def new_airplane(self, id, initial_values):
        lat = initial_values['lat']
        long = initial_values['lon']
        alt = initial_values['alt']
        head = 0
        airplane = self.__make_airplane__(lat,long,alt,head,id,
                self.Our_Airplane.coord_geo,self.Our_Airplane.coord_ecef, False)
        self.Other_Airplanes.append(airplane)

    def remove_airplane(self,id):
        for airplane in self.Other_Airplanes:
            if airplane.id == id:
                self.Other_Airplanes.remove(airplane)

    def exited(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.gameExit = True
                pg.quit()
        return self.gameExit

    def update(self, ref, others):
        new_ref_coord = {}
        my_head = ref['hpath']*pi/180
        new_ref_coord['Latitude'] =  ref['lat'] * pi / 180
        new_ref_coord['Longitude'] = ref['lon'] * pi / 180
        new_ref_coord['Altitude'] = ref['alt'] * 0.3048
        self.Our_Airplane.update_coord(new_ref_coord, my_head, own=True)
        for airplane in self.Other_Airplanes:
            for other in others:
                if airplane.id == other['id']:
                    new_coords = {}
                    new_coords['Latitude'] = other['lat']*pi/180
                    new_coords['Longitude'] = other['lon']*pi/180
                    new_coords['Altitude'] = other['alt']*0.3048
                    airplane.update_coord(new_coords, my_head,
                                            self.Our_Airplane.coord_geo.copy(),
                                            self.Our_Airplane.coord_ecef.copy())
                    airplane.v_z = other['GS_knots']*other['vpath']
        self.gD.fill(BACKGROUNG_COLOR)
        self.__draw_background__()
        self.__draw_ticks__(my_head)
        self.__set_tcas_status__()
        self.__draw_airplanes__()
        self.__draw_our_airplane__()
        self.__represent_data__(ref['GS_knots'], ref['TAS_knots'], my_head)
        ##  Draw envolving
        pgD.rect(self.gD, GREY, [0, 0, WIDTH, HEIGHT-75], 20)
        pg.display.update()
        self.clock.tick(SAMPLING_TIME)

    def __represent_data__(self,GS,TAS,head):
        ##  Add heading to display
        HDG_str = str(int(head*180/pi)) + 'º'
        font_size = int(WIDTH/40)
        f = font.SysFont('Lucida Console', font_size)
        HDG_text = f.render(HDG_str, False, GREEN)

        ##  Add groundspeed, TAS and range on display
        GS_str = 'GS  ' + str(int(GS))
        TAS_str = 'TAS ' + str(int(TAS))
        RNG_str = 'RNG ' + str(int(RANGE)) + 'NM'
        font_size = int(WIDTH/35)
        f = font.SysFont('Lucida Console', font_size)
        GS_text = f.render(GS_str, False, GREEN)
        TAS_text = f.render(TAS_str, False, GREEN)
        RNG_text = f.render(RNG_str, False, GREEN)

        rect = [WIDTH/2-WIDTH*0.07/2, AP_POS-D4/2+10, WIDTH*0.07, font_size+5]
        pgD.rect(self.gD, BLACK, rect, 0)
        pgD.rect(self.gD, WHITE, rect, 5)
        self.gD.blit(GS_text, [0.02*WIDTH, 0.02*WIDTH])
        self.gD.blit(TAS_text, [WIDTH*0.02, 0.02*WIDTH + 1.15*font_size])
        self.gD.blit(RNG_text, [WIDTH - WIDTH*0.16, 0.02*WIDTH])
        self.gD.blit(HDG_text, [WIDTH/2 - WIDTH*0.06/2, AP_POS - D4/2 + 13])

    def __draw_our_airplane__(self):
        a = [WIDTH/2, AP_POS+30]
        b = [WIDTH/2, AP_POS-10]
        pgD.line(self.gD, WHITE, a, b, 3)
        a = [WIDTH/2-10, AP_POS+25]
        b = [WIDTH/2+10, AP_POS+25]
        pgD.line(self.gD, WHITE, a, b, 5)
        a = [WIDTH/2-30, AP_POS]
        b = [WIDTH/2+30, AP_POS]
        pgD.line(self.gD, WHITE, a, b, 10)
        return

    def __draw_background__(self):
        ##  Draw equidistance lines
        self.__draw_dist_circle__(D1/2, 1)
        self.__draw_dist_circle__(D2/2, 1)
        self.__draw_dist_circle__(D3/2, 1)
        self.__draw_dist_circle__(D4/2, 8)
        ## Draw equidistance lines' distance in NM
        self.__draw_dist_numbers__(-70, 5, D1/2)
        self.__draw_dist_numbers__(-80, 10, D2/2)
        self.__draw_dist_numbers__(-83, 15, D3/2)
        self.__draw_dist_numbers__(-84.5, 20, D4/2)
        ## Draw lines of constant heading
        self.__draw_heading_lines__(0, 5)
        for head in [-135, -90, -45, 45, 90, 135]:
            self.__draw_heading_lines__(head, 1)
        return

    def __draw_heading_lines__(self, angle, line_width):
        angle = angle*pi/180
        point_1 = [WIDTH/2 + D1/2*sin(angle), AP_POS-D1/2*cos(angle)]
        point_2 = [WIDTH/2 + D4/2*sin(angle), AP_POS-D4/2*cos(angle)]
        pgD.line(self.gD, WHITE, point_1, point_2,line_width)
        return

    def __draw_dist_numbers__(self, angle, r, r_display):
        f = font.SysFont('Lucida Console', int(WIDTH/55))
        text_angle = angle*pi/180
        margin = 0.007*WIDTH
        text = f.render(str(r), False, WHITE)
        a = int(WIDTH/2 + r_display*sin(text_angle)+margin)
        b = int(AP_POS - r_display*cos(text_angle))
        self.gD.blit(text, [a, b])
        return

    def __draw_dist_circle__(self, r, line_width):
        loc_x = int(WIDTH/2) - int(r)
        loc_y = AP_POS - r
        arc = (loc_x,loc_y, 2*r, 2*r)
        pgD.arc(self.gD, WHITE, arc, -1.1*pi, pi, line_width)
        return

    def __draw_ticks__(self, head):
        inc = 30*pi/180
        for inc_head in range(-int(pi/inc), int(pi/inc)):
            ##  Draw ticks
            a = int(WIDTH/2 + D4/2 *sin(-head+inc_head*inc))
            b = int(AP_POS - D4/2*cos(-head+inc_head*inc))
            c = int(WIDTH/2 + (D4/2 + 20) *sin(-head+inc_head*inc))
            d = int(AP_POS - (D4/2 + 20)*cos(-head+inc_head*inc))
            pgD.line(self.gD, WHITE, [a, b], [c, d], 3)

            display_angle = (inc_head)*30 - 180
            if display_angle > 360:
                display_angle = display_angle - 360
            if display_angle < 0:
                display_angle = display_angle + 360
            ##  Display tick number
            disp_n = int(display_angle/10)
            if disp_n == 0 or disp_n == 18 or disp_n == 9 or disp_n == 27:
                f = font.SysFont('Lucida Console', int(WIDTH/30))
                if disp_n == 0:
                    tick_text = f.render('N', False, WHITE)
                elif disp_n == 18:
                    tick_text = f.render('S', False, WHITE)
                elif disp_n == 9:
                    tick_text = f.render('E', False, WHITE)
                else:
                    tick_text = f.render('W', False, WHITE)
            else:
                f = font.SysFont('Lucida Console', int(WIDTH/40))
                tick_text = f.render(str(disp_n), False, WHITE)

            a = int(WIDTH/2 + (D4/2 + 30)*sin(-head+(inc_head-int(pi/inc))*inc))
            b = int(AP_POS - (D4/2 + 45)*cos(-head+(inc_head-int(pi/inc))*inc))
            vertix = [a, b]
            if vertix[0] < WIDTH/2:
                font_size = WIDTH/45
                a = (D4/2 + 30)*sin(-head+(inc_head-int(pi/inc))*inc)
                a = a + WIDTH/2 - font_size*1.5
                b = AP_POS - (D4/2+45)*cos(-head+(inc_head-int(pi/inc))*inc)
                vertix = [int(a), int(b)]
            self.gD.blit(tick_text, vertix)
        return

    def __draw_airplanes__(self):
        for airplane in self.Other_Airplanes:
            x = int(airplane.coord_disp['x'])
            y = int(airplane.coord_disp['y'])
            rel_alt = int(airplane.relative_alt/0.3048)
            climb_status = self.__set_status__(airplane.v_z)
            if airplane.tcas_status == 0:
                pass
            elif airplane.tcas_status == 1:
                self.__otherAircraft__(x, y)
            elif airplane.tcas_status == 2:
                self.__proximateAircraft__(x, y, climb_status, rel_alt)
            elif airplane.tcas_status == 3:
                self.__drawTA__(x, y, climb_status, rel_alt)
            elif airplane.tcas_status == 4:
                self.__drawRA__(x, y, climb_status, rel_alt)

    @staticmethod
    def __set_status__(v_z):
        if v_z > 0:
            return 2
        elif v_z < 0:
            return 1
        else:
            return 0

    @staticmethod
    def __set_move__(own_id, relative_alt, other_id, status):
        new_checkmove = 'None'
        if status == 4:
            if relative_alt > 0 or (relative_alt == 0 and own_id > other_id):
                new_checkmove = 1
            elif relative_alt < 0 or (relative_alt == 0 and own_id < other_id):
                new_checkmove = 2
        if status == 3:
            new_checkmove = 3
        return new_checkmove

    def __otherAircraft__(self, x, y):
        pgD.polygon(self.gD, BLUE, [[x,y-15], [x-10,y],[x,y+15], [x+10,y]],3)
        return

    def __proximateAircraft__(self, x, y, status, relative_alt):
        pgD.polygon(self.gD, BLUE, [[x,y-15], [x-10,y],[x,y+15], [x+10,y]],0)
        if status==1:
            pgD.line(self.gD, BLUE, [x + 20, y - 5], [x + 20, y + 10], 2)
            pgD.line(self.gD, BLUE, [x + 20, y + 10], [x + 15, y + 5], 2)
            pgD.line(self.gD, BLUE, [x + 20, y + 10], [x + 25, y + 5], 2)
        elif status==2:
            pgD.line(self.gD, BLUE, [x + 20, y - 5], [x + 20, y + 10], 2)
            pgD.line(self.gD, BLUE, [x + 20, y - 5], [x + 15, y + 0], 2)
            pgD.line(self.gD, BLUE, [x + 20, y - 5], [x + 25, y + 0], 2)
        relative_alt = int(relative_alt/100)
        if abs(relative_alt) > 99:
            feet = str(99)
        else:
            feet = str(abs(relative_alt))

        f = font.SysFont('Lucida Console', 16)
        if abs(relative_alt*100) < 1000:
            feet = '0' + feet
        if relative_alt > 0:
            textsurface = f.render('+' + feet, False, BLUE)
        elif relative_alt < 0:
            textsurface = f.render('-' + feet, False, BLUE)
        else:
            textsurface = f.render(' '+ feet, False, BLUE)
        self.gD.blit(textsurface, (x - 12, y - 35))


    def __set_tcas_status__(self):
        for airplane in self.Other_Airplanes:
            old_status = airplane.tcas_status
            rel_alt = airplane.relative_alt
            Altitude = self.Our_Airplane.coord_geo['Altitude']
            if airplane.dist < 20*NM2m:# and Altitude > 1500*ft2m:
                if airplane.dist < 6*NM2m:
                    if airplane.dist < 3.3*NM2m:
                        if airplane.dist < 2.1*NM2m:
                            if rel_alt >= -600*ft2m and rel_alt <= 600*ft2m:
                               airplane.tcas_status = 4
                            elif rel_alt >= -850*ft2m and rel_alt <= 850*ft2m:
                                airplane.tcas_status = 3
                            else:
                                airplane.tcas_status = 2
                        else:
                            if rel_alt >= -850*ft2m and rel_alt <= 850*ft2m:
                                airplane.tcas_status = 3
                            else:
                                airplane.tcas_status = 2
                    else:
                        airplane.tcas_status = 2
                else:
                    airplane.tcas_status = 1
            else:
                airplane.tcas_status = 0
            status = airplane.tcas_status
            if (status==4 and old_status==3) or (status==3 and old_status==4):
                our_id = self.Our_Airplane.id
                move = self.__set_move__(our_id, rel_alt, airplane.id, status)
                self.__alert__(move)
            if airplane.tcas_status == 3 and old_status == 2:
                self.__alert__(0)
        return

    def __drawRA__(self,x,y,status,relative_alt): #Resolution Advisory
        side = 15
        vert_x = x - side/2
        vert_y = y + side/2
        pgD.rect(self.gD, RED, pg.Rect(vert_x,  vert_y, side, side))
        if status == 1:
            pgD.line(self.gD, RED, [x + 18, y + 0], [x + 18, y + 22], 2)
            pgD.line(self.gD, RED, [x + 18, y + 22], [x + 13, y + 17], 2)
            pgD.line(self.gD, RED, [x + 18, y + 22], [x + 23, y + 17], 2)
        elif status == 2:
            pgD.line(self.gD, RED, [x + 18, y + 7], [x + 18, y + 22], 2)
            pgD.line(self.gD, RED, [x + 18, y], [x + 13, y + 12], 2)
            pgD.line(self.gD, RED, [x + 18, y], [x + 23, y + 12], 2)
        relative_alt = int(relative_alt/100)
        feet = str(abs(relative_alt))
        f = font.SysFont('Lucida Console', 16)
        if relative_alt < 1000:
            feet = '0' + feet
        if relative_alt > 0:
            textsurface = f.render('+' + feet, False, RED)
        elif relative_alt < 0:
            textsurface = f.render('-' + feet, False, RED)
        else:
            textsurface = f.render(' '+ feet, False, RED)
        self.gD.blit(textsurface, (x - 15, y + 22))


    def __drawTA__(self, x, y, status, relative_alt):
        # Traffic Advisory
        # status=0->levelled
        # status=1->descending
        # status=2->ascending
        pgD.circle(self.gD, YELLOW, [x, y], 10)
        if status==1:
            pgD.line(self.gD, YELLOW, [x + 20, y - 8], [x +20, y + 10], 2)
            pgD.line(self.gD, YELLOW, [x + 20, y + 10], [x +15, y + 5], 2)
            pgD.line(self.gD, YELLOW, [x + 20, y + 10], [x +25, y + 5], 2)
        elif status==2:
            pgD.line(self.gD, YELLOW, [x + 20, y - 8], [x +20, y + 10], 2)
            pgD.line(self.gD, YELLOW, [x + 20, y - 8], [x + 15, y + 0], 2)
            pgD.line(self.gD, YELLOW, [x + 20, y - 8], [x + 25, y + 0], 2)
        relative_alt = int(relative_alt / 100)
        feet = str(abs(relative_alt))
        f = font.SysFont('Lucida Console', 16)
        if relative_alt<1000:
            feet = '0' + feet
        if relative_alt > 0:
            textsurface = f.render('+' + feet, False, YELLOW)
        elif relative_alt < 0:
            textsurface = f.render('-' + feet, False, YELLOW)
        else:
            textsurface = f.render(' ' + feet, False, YELLOW)
        self.gD.blit(textsurface, (x - 13, y + 9))

    @staticmethod
    def __alert__(move):
        list_sounds = []
        list_sounds.append('./../AlertsTCAS/Traffic.mp3')
        list_sounds.append('./../AlertsTCAS/DescendDescend.mp3')
        list_sounds.append('./../AlertsTCAS/ClimbClimb.mp3')
        list_sounds.append('./../AlertsTCAS/ClearOfConflict.mp3')
        if move !='None':
            pg.mixer.init(26000)
            pg.mixer.music.load(list_sounds[move])
            pg.mixer.music.play(0)
        return

    @staticmethod
    def __make_airplane__(coord_lat, coord_long, coord_alt, ref_head,
    airplane_id, coord_geo={}, coord_ecef={}, own=False):
        dict = {}
        dict['Latitude'] = coord_lat*pi / 180
        dict['Longitude'] = coord_long*pi / 180
        dict['Altitude'] = coord_alt
        airplane = Airplane(dict)
        airplane.id = airplane_id
        if own is False:
            airplane.update_coord(dict, ref_head, coord_geo, coord_ecef, own)
        else:
            airplane.update_coord(dict, ref_head, own=True)
        return airplane

    def __del__(self):
        pg.quit()
