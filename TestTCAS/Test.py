import TCAS
import pygame


if __name__ == '__main__':
    Tcas = TCAS.TCAS()

    #######################################
    #input simulation
    ref={"lat": 38.734060, "lon":-9.174937,"alt":100,"GS_knots":200,"hpath":160,"vpath":0,"TAS_knots":200}

    others=[{"lat":38.731307,"lon":-9.174439, "alt": 800, "GS_knots":5,"id":101},
            {"lat":38.841307,"lon":-9.346439, "alt": 100, "GS_knots":0,"id":102},
            {"lat":38.731307,"lon":-9.256439, "alt": 100, "GS_knots":0,"id":103},
            {"lat":38.714060,"lon":-9.154439, "alt": 900, "GS_knots":-5,"id":104}]
    #######################################

    others_values = [{'lat':0.1,'lon':0,'alt':-200,'GS_knots':100,'vpath':-0.1,"id":101,"TAS_knots":100},
                    {'lat':0.1,'lon':0.05,'alt':200,'GS_knots':100,'vpath':0,"id":102,"TAS_knots":100},
                    {'lat':0.1,'lon':-0.1,'alt':300,'GS_knots':100,'vpath':0,"id":103,"TAS_knots":100},
                    {'lat':0.1,'lon':-0.1,'alt':300,'GS_knots':100,'vpath':0,"id":104,"TAS_knots":100}]
    Tcas.new_airplane(101,others_values[0])
    Tcas.new_airplane(102,others_values[1])
    Tcas.new_airplane(103,others_values[2])
    Tcas.new_airplane(104,others_values[3])
    ref = {}
    ref['hpath'] = 0
    while not Tcas.exited():
        others_values[0]['lat'] += -0.001
        others_values[1]['lat'] += -0.0008
        others_values[2]['lat'] += -0.0007
        others_values[1]['lon'] += -0.0003
        others_values[2]['lon'] += +0.0007
        ref['lat'] = 0
        ref['lon'] = 0
        ref['alt'] = 0
        ref['GS_knots'] = 197
        ref['hpath'] += 0.0
        ref['vpath'] = 0
        ref['TAS_knots'] = 199
        Tcas.update(ref,others_values)

        Tcas.clock.tick(TCAS.SAMPLING_TIME)
