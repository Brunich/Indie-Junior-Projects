# Future Roadmap: AccessiGaming Cam

We've laid a solid foundation, but to truly make this accessible gaming camera indispensable, we need to push on a few key fronts over the next couple of quarters.

## Q3: Latency & Tracking Precision
Right now, the input delay is acceptable but not optimal for competitive or fast-paced games. 
- Implement a custom C++ extension for the computer vision loop to drop frame processing time by at least 30%.
- Refine the facial landmark detection model to handle low-light environments better. We're losing tracking accuracy when users play in the dark.

## Q4: Expanded Input Modalities
We need to move beyond just basic head tracking.
- Integrate blink and dwell clicking as native, first-class features. 
- Start R&D on eye-tracking integration using off-the-shelf webcams. It's a tough problem, but if we can get even a rudimentary implementation working, it opens up a ton of possibilities for users with severe mobility constraints.

## Q1 Next Year: UX & Integrations
- Overhaul the configuration UI. It needs to be dead simple to map facial gestures to keystrokes or gamepad inputs. 
- Build a companion app for mobile so users can adjust settings without alt-tabbing out of their game. 
- Explore native integration with OpenXR to support VR/AR use cases down the line.

Let's keep the focus on stability and speed. Every millisecond counts here.
