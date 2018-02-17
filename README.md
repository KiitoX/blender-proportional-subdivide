# Proportional Subdivide
Blender add-on to help subdivide edges with mathematical precision

This is especially useful for those who want to construct precise geometric shapes without wanting to worry about coding that in python.

## Example
For this we're going to place an octagon onto the side of a cube.

We know that we want all sides to be of equal length, we'll call that length `a`, with the pythagorean theorem we can calculate that each of the corner pieces is of length `a/sqrt(2)`. And that is basically all you need to know for this addon:

![menu example](example/menu.png)

With that we can then subdivide a single edge, or multiple edges at once:

![](example/cube1.png)

And finally we can use the knife tool [K] to cut out the octagon from the square face:

![](example/cube2.png)

Et voila! Eight equal length edges.

## Notes

If the subdivisions aren't symmetrical, you might have to use the reverse toggle for some edges, as the underlying mesh interface always returns the edge vertices in a fixed order that is seemingly random. 
