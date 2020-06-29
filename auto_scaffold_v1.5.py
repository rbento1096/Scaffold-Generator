import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

####### CHOOSE GEOMETRY      #######
# this allows the user to choose one of the available geometries -  currently only one is available
geometries = {
    1: "Cirular, Inner Dense Disk, Equally spaced Radiuses, Interconnecting Pores",
}

def select_geometry():
    print(geometries) #shows the possible geometries
    global geometry
    geometry = rs.GetInteger("Choose geometry number: ") 
select_geometry()

#######    BASE VARIABLES    #######

if geometry == 1:
    description = rs.GetInteger("You have selected a scaffold that consists of alternating gear-shaped layers and layers with concentrical circles with a dense central disk. This allows for pore interconnectability throughout the scaffold. You will now set the parameters. Press Enter to continue...")
    nozzle = rs.GetInteger("Type your nozzle diameter in micrometers:",) #nozzle diameter is a major parameter in 3D printing as it affects the model resolution.
    height = rs.GetInteger("Type your scaffold height in micrometers (WARNING: It must be a multiple of your nozzle diameter):",)
    while height < nozzle:
        print("Scaffold height must exceed nozzle diameter!")
        height = rs.GetInteger("Type your scaffold height in micrometers (WARNING: It must be a multiple of your nozzle diameter):",)
    if height%nozzle != 0:
        # as mentioned, nozzle limits the geometry's sizes and resolution. This warns the user that his height will be rounded to a value compatible with the nozzle.
        print("Height is not a multiple of the nozzle diameter. Height will be rounded to " + str(int(height/nozzle)*nozzle) + " micrometers")  
    layers = int(height/nozzle)
    origins = []
    for i in range(0,(layers+1),1): #this will create origins with coordinates: x=0, y=0 and with z starting at 0 and incrementing by nozzle diameter. 
                                    #layers+1 adds an additional origin that will serve as the endpoint of the vector that defines the last layer
        origins.append([0,0,(i*nozzle/1000)]) # diameter is divided by 1000 to convert from micrometers to milimeters (unit used in Rhinoceros)
    int_radius = rs.GetInteger("Enter the INNER radius, in micrometers, of the dense disk;",)
    ext_radius = rs.GetInteger("Enter the OUTER radius, in micrometers, of the dense disk:",)
    while ext_radius <= int_radius:
        print "external radius can't be smaller than internal radius. Enter a new value"
        ext_radius = rs.GetInteger("Enter the OUTER radius, in micrometers, of the dense disk:",)
    if (ext_radius-int_radius)%nozzle != 0: #if the difference between the internal and external radius is not compatible with the nozzle diameter...
        if int(ext_radius-int_radius/nozzle) == 0: # if that difference is smaller than the nozzle diameter:
            ext_radius = int_radius + nozzle
            print("External radius doesnt allow for nozzle compatibility. We have assumed the smallest disk diameter that was geometrically possible : " + str(ext_radius) + " micrometers")
        else:
            ext_radius = int_radius + int((ext_radius-int_radius)%nozzle) * nozzle # else just get the smallest value
            print("Your dense disk specifications were incompatible with this nozzle. We have given the closest value of " + str(ext_radius) + " micrometers to your external radius")
    ext_radius_perimeter = 2*ext_radius*(math.pi)
    tooth_nr = rs.GetInteger("Enter the number of teeth on the toothed layers:",)
    tooth_thick = rs.GetInteger("Enter the thickness of teeth on the toothed layers in micrometers(WARNING: It must be a multiple of your nozzle diameter):",)
    if tooth_thick%nozzle != 0: #again, same proceeding as before: make sure it is a multiple and, if not, assume the lowest value.
        tooth_thick = int(tooth_thick/nozzle)*nozzle
        if tooth_thick == 0:
            tooth_thick = nozzle
        print("Tooth thickness is incompatible with nozzle diameter. Changed to " + str(tooth_thick) + " micrometers")
    tooth_array_length = (tooth_thick)*tooth_nr #this is the length of all the teeth lined one by one
    while tooth_array_length > ext_radius_perimeter: # if the length of the lined teeth is greater than the ext_radius then the teeth will superimpose 
        print("Number of teeth or their thickness are superimposing. Change one or both values.") #although printing can still proceed, it is undesirable to haver superimposing elements
        tooth_nr = rs.GetInteger("Enter the number of tooths on the toothed layers:",)
        tooth_thick = rs.GetInteger("Enter the thickness of tooths on the toothed layers in micrometers(WARNING: It must be a multiple of your nozzle diamter):",)
        if tooth_thick%nozzle != 0: #once again, change the value until it works and use the same rounding strategy as before
            tooth_thick = int(tooth_thick/nozzle)*nozzle
            if tooth_thick == 0:
                tooth_thick = nozzle
            print("Tooth thickness is incompatible with nozzle diameter. Changed to " + str(tooth_thick) + " micrometers")
        tooth_array_length = (tooth_thick)*tooth_nr
    num_rad = rs.GetInteger("number of radiuses (WARNING: must be odd and two radiuses form a surface):",) 
    #this isn't very explicit. It's the total diameter of the scaffold. multiplying nozzle diameter by num rads we have this value. 
    #Need to change the variable name and functioning to be more user friendly -> ask just for the diameter and automate the rest 
    if num_rad%2 == 0:
        num_rad += 1 #if radiuses number is even then we won't be able to extrude a circle. Can't work if they are all equally spaced.
        print("You have chosen an even number of radiuses. We added another one so the scaffold is symmetrical. The scaffold diameter has increased by " + str(nozzle) + " micrometers")
    radius = [] 
    for i in range(0,num_rad): #this will add a list of radiuses for each circle in the circled layer. Explanation ahead.
        radius.append(ext_radius/1000+nozzle/1000*i)
    print("Teeth setup is valid. Preparing model...")


#######    CIRCULAR LAYER    #######

def circle_layer(origin1,origin2): # the function takes two origins - her origin and next layer's origin.
    path = rs.AddLine(origin1,origin2) #using the next layer's origin a vector is created (as mentioned before, this is why the num of origins is layers+1)
    int0 = rs.AddCircle(origin1,int_radius/1000) #this adds the circle that defined the inner radius of the dense disk
    ext0 = rs.AddCircle(origin1,ext_radius/1000) # and this the outer radius of the dense disk. Note that every time something is drawn it is converted to milimeters
    face0 = rs.AddPlanarSrf([int0,ext0]) #this adds a surface between the circles
    rs.ExtrudeSurface(face0,path) #this extrudes the surface along the vector made previously
    circles =[]
    for i in range(1,num_rad): # It was not possible to add the circles directly iteratively so I made this workaround: just put append them to an array.
        circles.append(rs.AddCircle(origin1,radius[i]))
    for i in range(0,num_rad): #and starting from the array call the circles again
        if i == num_rad-1: # notify that a circular layer has been completed
            print("circular layer complete.")
        elif i%2 == 0: #this will extrude a surface delimited by two consequential circles along the vector connecting the two origins, once again.
            face = rs.AddPlanarSrf([circles[i],circles[i+1]])
            rs.ExtrudeSurface(face,path)
        else: # after a circular surface is extruded, an empty space must precede the next surface. So we just print a warning
            print("spacing surface...")
    rs.DeleteObject(path) #the vector can be visually seen in the model, this cleans it.

#######    TOOTHED LAYER    #######

def tooth_layer(origin1,origin2): #same input as before, for the same reasons
    int0 = rs.AddCircle(origin1,int_radius/1000)  #the dense disk is equal along the whole scaffold, so this layer starts similarly.
    ext0 = rs.AddCircle(origin1,ext_radius/1000) 
    face0 = rs.AddPlanarSrf([int0,ext0])
    int1 = rs.AddCircle(origin1,ext_radius/1000) 
    ext1 = rs.AddCircle(origin1,radius[num_rad-1]) #this circle has the radius of the outermost circle = the scaffold's diameter. It will be used to "cut" the teeth
    face1 = rs.AddPlanarSrf([int1,ext1])
    path = rs.AddLine(origin1,origin2)
    #corte cuts the surface. it takes face1 as the surface to be cut, 2 is the number of dimensions to cut in, next is an array with the x and y intervals to cut. True deletes the unwanted surface.
    #radius[num_rad-1]-ext_radius/1000 is the radius of the scaffold
    #[(-tooth_thick/1000/2),(tooth_thick/1000/2)] one value is in the negative axis, the other in the positive. Summed together they equal tooth thickness
    # Rhinoceros had a strange way of interpreting the dimensions and their origin. This generated a rectangle with length = diameter and with the chosen thickness.
    corte = rs.TrimSurface(face1,2,([0,(radius[num_rad-1]-ext_radius/1000)],[(-tooth_thick/1000/2),(tooth_thick/1000/2)]),True) 
    magia0 = rs.ExtrudeSurface(face0,path) #extrudes the disk
    magia1 = rs.ExtrudeSurface(corte,path) #extrudes the cut rectangle
    # With the previous cut, however, we only had ONE tooth.
    for i in range(1,(tooth_nr)): #this will create tooth_nr - 1 teeth (we already had the original)
        degrees = (360/tooth_nr)*i #defines the angle each tooth will need to rotate in order to be equally spaced around the center circle
        radians = math.radians(degrees) #converts the degrees to radians
        c = math.cos(radians) #cosine
        s = math.sin(radians) #sine
        matrix = [] #the matrix that will define the (circular) path along which the teeth will be multiplied
        matrix.append( [c,-s, 0, 0] )
        matrix.append( [s, c, 0, 0] )
        matrix.append( [0, 0, 1, 0] )
        matrix.append( [0, 0, 0, 1] )
        if magia1: rs.TransformObject( magia1, matrix, copy = True ) #selects the tooth, the path and makes sure that it's a copy instead of just moving the object
    rs.DeleteObject(path) #again, delete the vector
    print("toothed layer complete.")

#######    BUILD    #######
####### geometry 1  #######
def build_geometry1(): #builds the first geometry
    for i in range(0,layers):
        if i == 0: #first layer has both types of layer superimposed on the cad model (here it's okay as they will form a single lid-like layer
            circle_layer(origins[i],origins[i+1])
            tooth_layer(origins[i],origins[i+1])
        elif i == layers-1: #the last one also has both to act as a lid
            circle_layer(origins[i],origins[i+1])
            tooth_layer(origins[i],origins[i+1])
        elif i%2 == 0: #alternating layers: the even layers will be circular
            circle_layer(origins[i],origins[i+1])
        else: #the odd layers will be gear-shaped
            tooth_layer(origins[i],origins[i+1])
    print("SUCCESS!!! The scaffold is printed.")

if geometry == 1:
    build_geometry1()
###########################
