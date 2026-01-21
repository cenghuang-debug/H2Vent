#Hydrogen dispersion at room temperature based on experiments by Gilles Bernard-Michel and Houssin-Agbomson 2017. The hydrogen volume flow rate is 210 NL/min; nozzle size is 27 mm.

#A slover rhoReactingBuoyantFoamSc for considering turbulent Schmidt number
#follow the step to compile the solver in your user directory
mkdir -p $WM_PROJECT_USER_DIR/applications/solvers/combustion/
cp -r rhoReactingBuoyantFoamSc $WM_PROJECT_USER_DIR/applications/solvers/combustion/
wclean
wmake
