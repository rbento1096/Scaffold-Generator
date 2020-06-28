import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

####### CHOOSE GEOMETRY      #######

geometries = {
    1: "Cirular, Inner Dense Disk, Equally spaced Radiuses, Interconnecting Pores",
}

def select_geometry():
    print(geometries)
    global geometry
    geometry = rs.GetInteger("Choose geometry number: ") 
select_geometry()

#######    BASE VARIABLES    #######

if geometry == 1:
    description = rs.GetInteger("You have selected a scaffold that consists of alternating gear-shaped layers and layers with concentrical circles. This allows for pore interconnectability throughout the scaffold. You will now set the parameters. Press Enter to continue...")
    nozzle = rs.GetInteger("Type your nozzle diameter in micrometers:",)
    height = rs.GetInteger("Type your scaffold height in micrometers (WARNING: It must be a multiple of your nozzle diameter):",)
    while height < nozzle:
        print("Scaffold height must exceed nozzle diameter!")
        height = rs.GetInteger("Type your scaffold height in micrometers (WARNING: It must be a multiple of your nozzle diameter):",)
    if height%nozzle != 0:
        print("Height is not a multiple of the nozzle diameter. Height will be rounded to " + str(int(height/nozzle)*nozzle) + " micrometers")
    layers = int(height/nozzle)
    origins = []
    for i in range(0,(layers+1),1): #+1 para que comece no 0 e +1 de novo para faze o path do ultimo layer
        origins.append([0,0,(i*nozzle/1000)])
    int_radius = rs.GetInteger("Enter the INNER radius, in micrometers, of the dense disk;",)
    ext_radius = rs.GetInteger("Enter the OUTER radius, in micrometers, of the dense disk:",)
    while ext_radius <= int_radius:
        print "external radius can't be smaller than internal radius. Enter a new value"
        ext_radius = rs.GetInteger("Enter the OUTER radius, in micrometers, of the dense disk:",)
    if (ext_radius-int_radius)%nozzle != 0:
        if int(ext_radius-int_radius/nozzle) == 0:
            ext_radius = int_radius + nozzle
            print("External radius doesnt allow for nozzle compatibility. We have assumed the smallest disk diameter that was geometrically possible : " + str(ext_radius) + " micrometers")
        else:
            ext_radius = int_radius + int((ext_radius-int_radius)%nozzle) * nozzle
            print("Your dense disk specifications were incompatible with this nozzle. We have given the closest value of " + str(ext_radius) + " micrometers to your external radius")
    ext_radius_perimeter = 2*ext_radius*(math.pi)
    tooth_nr = rs.GetInteger("Enter the number of teeth on the toothed layers:",)
    tooth_thick = rs.GetInteger("Enter the thickness of teeth on the toothed layers in micrometers(WARNING: It must be a multiple of your nozzle diameter):",)
    if tooth_thick%nozzle != 0:
        tooth_thick = int(tooth_thick/nozzle)*nozzle
        if tooth_thick == 0:
            tooth_thick = nozzle
        print("Tooth thickness is incompatible with nozzle diameter. Changed to " + str(tooth_thick) + " micrometers")
    tooth_array_length = (tooth_thick)*tooth_nr
    while tooth_array_length > ext_radius_perimeter:
        print("Number of teeth or their thickness are superimposing. Change one or both values.")
        tooth_nr = rs.GetInteger("Enter the number of tooths on the toothed layers:",)
        tooth_thick = rs.GetInteger("Enter the thickness of tooths on the toothed layers in micrometers(WARNING: It must be a multiple of your nozzle diamter):",)
        if tooth_thick%nozzle != 0:
            tooth_thick = int(tooth_thick/nozzle)*nozzle
            if tooth_thick == 0:
                tooth_thick = nozzle
            print("Tooth thickness is incompatible with nozzle diameter. Changed to " + str(tooth_thick) + " micrometers")
        tooth_array_length = (tooth_thick)*tooth_nr
    num_rad = rs.GetInteger("number of radiuses (WARNING: must be odd and two radiuses form a surface):",)
    if num_rad%2 == 0:
        num_rad += 1
        print("You have chosen an even number of radiuses. We added another one so the scaffold is symmetrical. The scaffold diameter has increased by " + str(nozzle) + " micrometers")
    radius = []
    for i in range(0,num_rad):
        radius.append(ext_radius/1000+nozzle/1000*i)
    print("Teeth setup is valid. Preparing model...")


#######    CIRCULAR LAYER    #######

def circle_layer(origin1,origin2):
    path = rs.AddLine(origin1,origin2)
    int0 = rs.AddCircle(origin1,int_radius/1000)
    ext0 = rs.AddCircle(origin1,ext_radius/1000)
    face0 = rs.AddPlanarSrf([int0,ext0])
    rs.ExtrudeSurface(face0,path)
    circles =[]
    for i in range(1,num_rad):
        circles.append(rs.AddCircle(origin1,radius[i]))
    for i in range(0,num_rad):
        if i == num_rad-1:
            print("circular layer complete.")
        elif i%2 == 0:
            face = rs.AddPlanarSrf([circles[i],circles[i+1]])
            rs.ExtrudeSurface(face,path)
        else:
            print("spacing surface...")
    rs.DeleteObject(path)

#######    TOOTHED LAYER    #######

def tooth_layer(origin1,origin2):
    int0 = rs.AddCircle(origin1,int_radius/1000)
    ext0 = rs.AddCircle(origin1,ext_radius/1000)
    face0 = rs.AddPlanarSrf([int0,ext0])
    int1 = rs.AddCircle(origin1,ext_radius/1000)
    ext1 = rs.AddCircle(origin1,radius[num_rad-1])
    face1 = rs.AddPlanarSrf([int1,ext1])
    path = rs.AddLine(origin1,origin2)
    corte = rs.TrimSurface(face1,2,([0,(radius[num_rad-1]-ext_radius/1000)],[(-tooth_thick/1000/2),(tooth_thick/1000/2)]),True)
    magia0 = rs.ExtrudeSurface(face0,path)
    magia1 = rs.ExtrudeSurface(corte,path)
    for i in range(1,(tooth_nr)): # 1 a menos mas temos o original
        degrees = (360/tooth_nr)*i
        radians = math.radians(degrees)
        c = math.cos(radians)
        s = math.sin(radians)
        matrix = []
        matrix.append( [c,-s, 0, 0] )
        matrix.append( [s, c, 0, 0] )
        matrix.append( [0, 0, 1, 0] )
        matrix.append( [0, 0, 0, 1] )
        if magia1: rs.TransformObject( magia1, matrix, copy = True )
    rs.DeleteObject(path)
    print("toothed layer complete.")

#######    BUILD    #######
####### geometry 1  #######
def build_geometry1():
    for i in range(0,layers):
        if i == 0:
            circle_layer(origins[i],origins[i+1])
            tooth_layer(origins[i],origins[i+1])
        elif i == layers-1:
            circle_layer(origins[i],origins[i+1])
            tooth_layer(origins[i],origins[i+1])
        elif i%2 == 0:
            circle_layer(origins[i],origins[i+1])
        else:
            tooth_layer(origins[i],origins[i+1])
    print("SUCCESS!!! The scaffold is printed.")


build_geometry1()
###########################