# Snoopy Chase

## PURPOSE
The purpose of `snoopy_chase.py` is to provide a playful desktop application where a Snoopy image dynamically chases the user’s mouse 
pointer around the application window. It is designed as a fun demonstration of Python GUI programming with Tkinter and Pillow, 
highlighting smooth animation, image handling, and interactive input.

## DESCRIPTION
When launched, the application prompts the user to choose which Snoopy image they would like to use (for example, a flying Snoopy or a 
grabbing Snoopy). The chosen image is displayed at the center of the window and immediately begins to "chase" the mouse pointer. The 
movement is smoothed using easing and capped velocity, so Snoopy glides naturally toward the cursor instead of jumping abruptly. When 
Snoopy reaches the pointer, the pointer will disappear. The program ensures that the character remains fully visible inside the window 
boundaries, even when the window is resized.

Beyond simply showing an image, the application demonstrates interactive graphics techniques such as sprite scaling, boundary clamping, 
and real-time user tracking. Users can close the application at any time with the Escape key. The structure of the code is modular, 
making it easy to extend with additional images, movement behaviors, or game-like features. This combination of lighthearted visuals and 
accessible Python code makes the project both entertaining to run and educational for those learning about GUI animation.
