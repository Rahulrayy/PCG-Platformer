"""
Sits between the generator and the  game world
tracks which chunk the player is currently in, asks the generator queue for the next chunk when the player gets close to the right edge,and swaps it into the world when ready.(take cure that ending of chunk a== start of chunk a+1
 Tells the camera the new world width and handles the coordinate offset so chunks stitch together well

"""