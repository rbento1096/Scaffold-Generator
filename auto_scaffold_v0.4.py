import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

'''DISCLAIMER: This script was developed just for quick testing and was never properly written (adding functions, adjusting for scalability, etc...)
since the printer couldn't successfuly convert some CAD geometries to G Code. Nonetheless I put it here so I can improve it in case I need it in the future
(and have a better printer...). As is, it generates a cylindrical scaffold with interconnected pores and a dense disk (useful in spinal implants)'''

#######    BASE VARIABLES    #######

# diameter of the extruded material
nozzle = rs.GetInteger("Type your nozzle diameter in micrometers:",) 
height = rs.GetInteger("Type your scaffold height in micrometers (WARNING: It must be a multiple of your nozzle diameter):",)
while height < nozzle:
    print("Scaffold height must exceed nozzle diameter!")
    height = rs.GetInteger("Type your scaffold height in micrometers (WARNING: It must be a multiple of your nozzle diameter):",)

# height is dependant of extruder diameter in a layer-by-layer assembly
if height % nozzle != 0:
    print("Height is not a multiple of the nozzle diameter. Height will be rounded to " + str(int(height/nozzle)*nozzle)+ + " micrometers") 

layers = int(height/nozzle)

# adds the circle origin for every layer
origins = []
for i in range(0, (layers+1)):  
    # diameter is divided by 1000 to convert from micrometers to milimeters (unit used in Rhinoceros)
    origins.append([0, 0, (i*nozzle/1000)]) 

int_radius = rs.GetInteger("Enter the INNER radius, in micrometers, of the dense disk;",)
ext_radius = rs.GetInteger("Enter the OUTER radius, in micrometers, of the dense disk:",)

while ext_radius <= int_radius:
    print "external radius can't be smaller than internal radius. Enter a new value"
    ext_radius = rs.GetInteger("Enter the OUTER radius, in micrometers, of the dense disk:",)

if (ext_radius - int_radius) % nozzle != 0: 

    if int(ext_radius - int_radius / nozzle) == 0: 
        ext_radius = int_radius + nozzle
        print("External radius doesnt allow for nozzle compatibility. We have assumed the smallest disk diameter that was geometrically possible : " + str(ext_radius) + " micrometers")
    else:
        ext_radius = int_radius + int((ext_radius - int_radius) % nozzle) * nozzle 
        print("Your dense disk specifications were incompatible with this nozzle. We have given the closest value of " + str(ext_radius) + " micrometers to your external radius")

ext_radius_perimeter = 2 * ext_radius * math.pi

tooth_nr = rs.GetInteger("Enter the number of teeth on the toothed layers:",)
tooth_thick = rs.GetInteger("Enter the thickness of teeth on the toothed layers in micrometers(WARNING: It must be a multiple of your nozzle diameter):",)


if tooth_thick % nozzle != 0: 
    tooth_thick = int(tooth_thick/nozzle) * nozzle
    if tooth_thick == 0:
        tooth_thick = nozzle
    print("Tooth thickness is incompatible with nozzle diameter. Changed to " + str(tooth_thick) + " micrometers")

tooth_array_length = tooth_thick * tooth_nr 

# if the length of the lined teeth is greater than the ext_radius then the teeth will superimpose 
while tooth_array_length > ext_radius_perimeter: 
    print("Number of teeth or their thickness are superimposing. Change one or both values.")
    tooth_nr = rs.GetInteger("Enter the number of tooths on the toothed layers:",)
    tooth_thick = rs.GetInteger("Enter the thickness of tooths on the toothed layers in micrometers(WARNING: It must be a multiple of your nozzle diamter):",)
    
    if tooth_thick % nozzle != 0: 
        tooth_thick = int(tooth_thick / nozzle) * nozzle
        if tooth_thick == 0:
            tooth_thick = nozzle
        print("Tooth thickness is incompatible with nozzle diameter. Changed to " + str(tooth_thick) + " micrometers")
    tooth_array_length = tooth_thick * tooth_nr

num_rad = rs.GetInteger("number of radiuses (WARNING: must be odd and two radiuses form a surface):",) 

if num_rad % 2 == 0:
    #if number of radiuses is even then we won't be able to extrude a circle.
    num_rad += 1 
    print("You have chosen an even number of radiuses. Another was added so the scaffold is symmetrical. The scaffold diameter has increased by " + str(nozzle) + " micrometers")

radius = [] 
for i in range(0, num_rad): 
    radius.append(ext_radius / 1000 + nozzle / 1000 * i)

print("Teeth setup is valid. Preparing model...")


#######    CIRCULAR LAYER    #######

# the function takes two origins - her origin and next layer's origin.
def circle_layer(origin1, origin2): 
    #using the next layer's origin a vector is created
    path = rs.AddLine(origin1,origin2) 
    # this adds the circle that defines the inner radius of the dense disk
    # Note that every time something is drawn it is converted to milimeters
    int0 = rs.AddCircle(origin1,int_radius / 1000) 
    # and this the outer radius of the dense disk. 
    ext0 = rs.AddCircle(origin1,ext_radius / 1000) 
    #this adds a surface between the circles
    face0 = rs.AddPlanarSrf([int0, ext0]) 
    #this extrudes the surface along the vector made previously
    rs.ExtrudeSurface(face0, path) 

    circles =[]
    # It was not possible to add the circles directly iteratively so I made this workaround: start by appending them to an array.
    for i in range(1, num_rad): 
        circles.append(rs.AddCircle(origin1, radius[i]))

    #and starting from the array call the circles again
    for i in range(0, num_rad): 
        if i == num_rad - 1: 
            print("circular layer complete.")

        # extrudes a surface delimited by two circles
        elif i % 2 == 0: 
            face = rs.AddPlanarSrf([circles[i], circles[i + 1]])
            rs.ExtrudeSurface(face,path)

        # does nothing, skipping a circle and creating an empty space
        else: 
            print("spacing surface...")

    # deletes the vector for aesthetic purposes
    rs.DeleteObject(path) 

#######    TOOTHED LAYER    #######

def tooth_layer(origin1, origin2): 
    int0 = rs.AddCircle(origin1, int_radius / 1000)  
    ext0 = rs.AddCircle(origin1, ext_radius / 1000) 
    face0 = rs.AddPlanarSrf([int0, ext0])

    int1 = rs.AddCircle(origin1, ext_radius / 1000) 
    #this circle has the radius of the outermost circle = the scaffold's diameter. It will be used to "cut" the teeth
    ext1 = rs.AddCircle(origin1, radius[num_rad - 1]) 
    face1 = rs.AddPlanarSrf([int1, ext1])
    path = rs.AddLine(origin1, origin2)

    # cuts a rectangle with length = scaffold radius - external disk radius and height = tooth thickness
    corte = rs.TrimSurface(face1, 2, ([0, (radius[num_rad - 1] - ext_radius / 1000)], [(-tooth_thick / 1000 / 2),(tooth_thick / 1000 / 2)]), True) 
    # extrudes the disk
    magia0 = rs.ExtrudeSurface(face0,path) 
    # extrudes the cut rectangle
    magia1 = rs.ExtrudeSurface(corte,path) 

    # We now need another tooth_nr - 1 teeth
    for i in range(1, (tooth_nr)): 

        # defines the angle each tooth will need to rotate in order to be equally spaced around the center circle
        degrees = (360 / tooth_nr) * i 
        radians = math.radians(degrees) 
        c = math.cos(radians) 
        s = math.sin(radians) 

        # the matrix that will define the (circular) path along which the teeth will be multiplied
        matrix = [] 
        matrix.append( [c,-s, 0, 0] )
        matrix.append( [s, c, 0, 0] )
        matrix.append( [0, 0, 1, 0] )
        matrix.append( [0, 0, 0, 1] )

        # copies the rectangular alongside the circular path defined by the matrix
        if magia1: rs.TransformObject( magia1, matrix, copy = True ) 

    # delete the vector
    rs.DeleteObject(path) 
    print("toothed layer complete.")

#######    BUILD    #######

for i in range(0,layers):
    # first and last layers will have both layer types superimposed to create a cylindrical contour
    if i == 0: 
        circle_layer(origins[i],origins[i+1])
        tooth_layer(origins[i],origins[i+1])
    elif i == layers-1: 
        circle_layer(origins[i],origins[i+1])
        tooth_layer(origins[i],origins[i+1])

    #alternating layers: the even layers will be circular
    elif i%2 == 0: 
        circle_layer(origins[i],origins[i+1])
    #the odd layers will be gear-shaped
    else: 
        tooth_layer(origins[i],origins[i+1])

print("SUCCESS!!! The scaffold is printed.")


