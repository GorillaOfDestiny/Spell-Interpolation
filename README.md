# Spell Interpolation

This is the code used in the "Spell Interpolation" videos by the Gorilla of Destiny (@gorillaofdestiny on tiktok, GorillaOfDestiny on YouTube). The basic idea is that we can describe every spell with Six Attributes, these attributes are themselves described by 6 aspects. 

There are 20 total aspects, where they act as positive/negative pairs so we have 10 unique axes. These are (with negatives in brackets):

- Beyond (Within)
- Heat (Cold)
- Light (Dark)
- Life (Death)
- Prodigious (Diminutive)
- Energy (Potential)
- Extrospection (Introspection)
- Flexibility (Rigidity)
- Hope (Hopelessness)
- Movement (Stagnancy)

These then describe aspects as, effectively, 10-dimensional vectors between which we can interpolate. An example interpolating between 2 Hope and 2 Heat can be seen in the figure below:

![alt text](https://github.com/GorillaOfDestiny/Spell-Interpolation/blob/main/plots/InteprolationExample_Annotated_NotTransparent.png?raw=true)

What the main file `interpolation.py` does is provide the functions used to calculate the interpolations. Only Cold and Necrotic damage types provide a direct interpolation and so that is the example. This would be boring if that's all we got so we also round to whole numbers and provide the distance to the nearest whole-valued point to the line during interpolation.

There is always a chance I'm being stupid so if there's any code issues let me know. Due to time issues I haven't made this terribly usable but I've tried to explain the most difficult bit of maths.

If you find any major issues feel free to email me or raise them in the github. I'll appreciate it forever.
