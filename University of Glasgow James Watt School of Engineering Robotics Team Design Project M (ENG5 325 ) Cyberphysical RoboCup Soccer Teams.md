University of Glasgow
James Watt School of Engineering
Robotics Team Design Project M (ENG5 325 )
Cyberphysical RoboCup Soccer Teams
Introduction

Robotic competitions have become extremely popular over the last few decades. Some of the most
popular competitive activities have involved the replication of sporting events e.g. robotic Olympics,
swimming, soccer. This particular project will focus on the design and development of robotic teams
for a soccer competition based on RoboCup leagues and rules (see Figure 1).

(a) Wheeled robots for RoboCup Soccer
(b) RoboCup Humanoid Soccer
Figure 1 : RoboCup Soccer Competitions
The particular purpose of this project is to design and develop virtual soccer teams and a virtual
environment for the teams to play on. These teams and the virtual playing environment will represent
the same entities and environment used in the real competitions.

This project will involve a two-stage process

Develop a simulation of your teams and their playing environment, and use this simulation to
design and develop the behavioural algorithms for your team members
Test your behavioural algorithms on hardware (humanoid robots)
Problem Specification

The Teams

In this project the robot players shall be humanoid robots based on the construction, actuation,
dynamics and kinematics of a NAO6 robot (see Figure 2).

Following the rules and guidelines for the KidSize Humanoid Soccer League
(https://humanoid.robocup.org/), each team will consist of 4 humanoid robots. These robots will
replicated the motion and actions of real soccer players e.g. kick the ball, dribble, pass the ball, run,
intercept.

(a) NAO6 Red & Blue
(b) NAO6 Schematic
Figure 2 : NAO6 Robots
Within each team the robots will exhibit different types of behaviour depending on the function of
the robot within the team and the state of play. These are:

Striker – This behaviour focusses on scoring points by kicking the ball into the opposing team’s goal.
The strikers could exhibit more aggressive behaviour and will be goal focussed when the team has
the ball. When the team does not have the ball then the striker behaviour will seek to intercept and
gain control of the ball.

Defender – This behaviour focusses on defending their team’s half of the pitch and the goal area. The
defender behaviour could be defensive in nature in that its primary function is to prevent the opposing
team from getting the ball near to the defending team’s goal. The range of the defender could extend
depending on the current situation of play.

Goalkeeper – This behaviour focusses on guarding the goal and preventing the opposing team from
scoring.

Whether your team has specific set formations, i.e. specific behaviours are assigned to particular
robots within the team and this does not change, or there is a dynamic allocation of behaviour, i.e.
behaviours change depending on the position of the robot on the pitch, all depends on your design for
the team. In addition, the team must follow the general rules of soccer as outlined by RoboCup.

Control Guidance of Robots

The control, guidance and navigation of the robots must be totally autonomous with no input from an
external operator. The robots should react to the state of play during a match and adopt an appropriate
behaviour. Design of the control, guidance and navigation system for each robot is a key aspect for
the project. The specification of the control system is determined by the performance requirements
for each playing behaviour and how the robot responds to the current state of play.

The Pitch or Field of Play

The dimensions of the Pitch for the KidSize Humanoid competition are 9m by 6m. The line spacing
and configuration is shown in Figure 3 below.

Figure 3 : Pitch Markings
The particular measurements and dimension of this pitch are shown in Table 1:

Table 1: Pitch Dimensions
Code Description Measurement
A Pitch length 9m
B Pitch width 6m
C Goal depth 0.6m
D Goal width 2.6m
Goal height 1.2m
E Goal area length 1m
F Goal area width 3m
G Penalty mark distance 1.5m
H Centre circle diameter 1.5m
I Border strip width 1m
J Penalty area length 2m
K Penalty area width 5m
This pitch is the main operating environment for your robot teams and they should function
appropriately within its confines.

The ball
The ball is taken to be similar to FIFA Ball Size 1 in dimensions which is 45cm in circumference.
This relates to approximately 14 cm in diameter. The colour of the ball can be black and white
hexagons or bright orange.

Project Management

Project management is the application of processes, skills, knowledge and experience to achieve
specific objectives and outcomes within a project. Every industry and every company have its own
favoured technique that it has tailored its processes and management structure. Fundamentally,
project management is used to produce a final deliverable in a finite timescale and budget. Some of
the main factors that are considered in most project management approaches are:

Stewardship – responsibility for managing resources.
Teamwork – working well together.
Systems Thinking – understanding how to divide the project into achievable workpackages of
work.
Leadership – guiding and motivating the project team.
Quality and Risk Focus – ensuring quality in the deliverables and mitigating associated risks.
Change Management – being resilient and adaptable so that you can manage change effectively.
Although there are numerous project management techniques, the two that are used widely in various
industries. These are the V-model and Waterfall model , which are described below:

V-model is a graphical representation of a system development lifecycle.
Waterfall model is a sequential process that outlines a system development lifecycle.
Each of these is outlined in Appendix B.

In your teams you will adopt and implement a project management approach and appropriate
management structure in order to satisfy the design specifications for this project. Each stage of your
chosen approach has its own associated deliverables and milestones that have to be completed
successfully and given to your project supervisors. It follows that your chosen approach can be used
as the basis for constructing a timing diagram (e.g. a Gantt chart) for your team to follow. This will
enable you to schedule your work, complete each identified workpackage and deliver the project
milestones in sufficient time and related cost. Also it will allow you to determine the Critical Design
Reviews that will allow you to progress onto other stages of the project or integrate deliverables for
different stages together.

Continual Reporting and Estimating Costs

In order to monitor the progress being made by the team and the amount of effort being applied by
each individual, a Time Allocation Record (TAR) will be completed by each team at the end of each
2 week period and delivered at the project supervisor’s meeting. This form will indicate the amount
of time that each member of the team has spent on the specified milestones for that period. The time
indication will be used to assess the individual contribution to the project and the overall staff costs.

The staff costs have been set at £ 25 0 per hour for this project. In addition, the cost of additional
expert help have been set at £1 25 0 per hour (this does not include consultation at weekly meetings).
An estimate of the total cost for the project should be put together during the Requirements stage
using the timing diagram (Gantt chart) that your team puts together. Both should be presented at your
first meeting with your supervisor.

The accurate record of the actual time resource used during the project will be collected using the
TARs outlined above. This can be used to calculate the actual costings in terms of staff and expert
help. These will be analysed in your report and a comparison against your estimates made.

Design Review Presentation

The Design Review Presentation will take place during the week commencing 2 nd February 202 6.
The purpose of the Design Review Presentation is to pitch the design of your completed simulation
and analysis of the behavioural characteristics developed for your teams. This presentation should be
10 minutes long including the demonstration. In addition, there will be 5 minutes for questions after
the presentation. The purpose of these pitch presentations is to ascertain if your team have completed
Stage 1 of the project i.e. produced an accurate simulation environment and developed and tested the

behavioural characteristics of your football teams. If your team has satisfied the requirements for
Stage 1 then they will be allowed to progress on to Stage 2: Hardware Implementation.

Final Reporting and Deliverables

The final evaluation of the project will be through a written report and an oral presentation. Each
team should produce a separate report that gives a clear and concise account of the design process
and evaluation of their Robotic Soccer Teams and their playing environment. In addition to providing
appraisal of the performance of the virtual soccer system, the report should provide an estimate of the
cost of developing this design and assessment of how well the team worked together. Individual
contributions to the project work, report and presentation should be indicated in the report and during
the presentation.

The completed reports should be submitted via the Moodle page for this course during the submission
window between 20th and 24th April 2026.

Each team will give an oral presentation that outlines the salient points of their report. The
presentation will be 20 minutes long with 5 minutes for questioning. Every member of the team will
be expected to deliver at least one part of the presentation. The presentations shall be held during the
week beginning 23 rd March 2026. Time and venue to be announced.

Please note that the University’s plagiarism policy applies to the material presented in the team reports
and presentations.

Peer Review Report

Each team member will be asked to complete a Peer Review Report for the Pitch Presentation and at
the end of the project. These reports will allow each team member to give peer and self-review
regarding the contributions made by all the members within their team. These reviews will be taken
into consideration during the assessment of the project.

Assessment Mark

Each student will receive an individual mark for this course, which will be determined through the
following components:

Report (60% - Team mark)
Teamworking (30% - Individual element of mark)
Presentations (10% - Team mark (3% from the Design Review Presentation and 7% from the
Final Presentation))
The teamworking element is determined through a combination of the TAR data, weekly meeting
assessment and peer review. Individual components of the report and presentation will be determined
using peer review weighting.

Dr McGookin
October 202 5

APPENDICES
APPENDIX A: Useful Webpages

RoboCup main webpage: https://www.robocup.org/

RoboCup Humanoid Soccer webpage: https://humanoid.robocup.org/

RoboCup Humanoid Soccer Rules: https://humanoid.robocup.org/wp-content/uploads/RC-HL-

2025 - Rules.pdf

NAO6 Robot Webpage: https://www.softbankrobotics.com/emea/en/nao

Matlab Onramp: https://uk.mathworks.com/learn/tutorials/matlab-onramp.html

Simulink Onramp: https://uk.mathworks.com/learn/tutorials/simulink-onramp.html

Stateflow Onramp: https://uk.mathworks.com/learn/tutorials/stateflow-onramp.html

Robot operating System: https://www.ros.org/

APPENDIX B: Project Management Techniques.

Appendix B.1: V-model Systems Development Lifecycle

The V-model (or sometimes called the V Diagram ) is a graphical representation of the design and
implementation process for a product or system (see Figure 5 ).

Figure 4 : V-model Based Project Plan
A typical V Diagram describes the stages involved in firstly designing a system (represented by the
initial downward stroke of the V) and then developing a physical product that can be brought to
market (represented by the upward stroke of the V). In this particular case the design part of the
project are the simulation based stages that will enable your team to produce an accurate simulation
testbed and behavioural characters for your robot soccer players. The development stages will allow
the performance of your design to be assessed through implementation on the actual test rig. Each
stage illustrated in Figure 5 is described in detail below:

Specification provides the team with the design outline for the project, which is presented in this
document and given in the initial project briefing.

Requirements stage allows the team to outline what is needed from each part of the system and the
resources needed for the complete development. Also involves the project planning, team structure
definition and time management activities.

Modelling & Validation involves the development of a validated simulation model (or digital twin)
describing the dynamic characteristics of the NAO6 robots, the ball and the pitch. The resulting
simulation provides the testbed environment that will be used to design and evaluate the control and
behaviour algorithms for your robot team.

Control & Behaviour is the main stage where the control and behaviour algorithms are developed.
Also, this is where the algorithms are tested and optimised.

Software Design of Robot Behaviours is the final signing off stage where the particulars of the
simulation design are presented. If the design is not satisfactory then the team will have to return to
earlier stages and rectify the problems with the behavioural designs.

SPECIFICATION
SOFTWARE DESIGN OF ROBOT BEHAVIOURS
REQUIREMENTS
MODELLING & VALIDATION
CONTROL & BEHAVIOUR
OPERATION
FIELD TEST
SYSTEM TEST
IMPLEMENTATION
Implementation involves the transfer of the software design into the hardware environment. This
enables the robot behaviours to be tested on the real NAO6 robots.

System Test is a crucial stage for evaluating the simulation-based designs on the actual hardware that
they are supposed to be controlling. This allows any problems caused by discrepancies in the
simulation to be compensated for and the design modified accordingly.

Field Test involves the final tests for your robot soccer team behaviours using an appropriate
experimental test regime.

Operation usually represents the production stage for the final tested product. In this case it will
involve the reporting activities i.e. the delivery of the final written report and final oral presentation.

Appendix B.2: Waterfall

A typical Waterfall Diagram describes the stages or workpackages involved in designing, evaluating
and testing a system. In this particular case the stages of the project are the simulation based stages
that will enable your team to produce a virtual humanoid robot soccer team and playing environment.
The development stages will allow the performance of your design to be assessed by means of an
appropriate test schedule for each stage. Each stage illustrated in Figure 5 is described in detail below:

Figure 5 : Waterfall Based Project Plan
Specification provides the team with the design outline for the project, which is presented in this
document and given in the initial project briefing.

Requirements stage allows the team to outline what is needed from each part of the system and the
resources needed for the complete development. Also involves the project planning and time/cost
management activities.

Modelling involves the development of a model describing the motion characteristics of the robot
players and the ball. These model provides the simulation entities that will be used as the basis of
your virtual soccer match.

Control & Guidance determines the lower level control and guidance behaviour of the robots. These
systems are used to provide the robots with the fundamental controlled motion needed to perform the
primary functions for the player types.

Algorithm Development involves the development of the algorithms that determine the behaviour and
interaction of the robots with other robots, the ball and the playing environment. These high level
algorithms should take into consider the behaviour of each player type as well as restrictions imposed
by the environment and the competition rules.

Specification
Requirements
Modelling
Control & Guidance
Algorithm Development
Environment Development
Operation
Environment Development involves the development of the playing environment and the visualisation
of the players, environment and ball. This defines the workspace for the robots and their operation
environment. The visualisation should be such that it accurately represents the play during the match
between 2 teams.

Operation represents the production stage for the final tested product. In this case it will involve the
reporting activities i.e. the delivery of the final written report and the final oral presentation.