# OASYS1-SHADOW4

### DO NOT INSTALL: this add-on is under development and highly unstable.

## Alpha tests
A collection of workspaces are being created containing parallel branches of simulations with shadow3 and shadow4. They are in the repository https://github.com/oasys-kit/shadow4workspaces

If involved in the alpha testing, please report issues in https://github.com/oasys-kit/shadow4/issues

## OASYS1-shadow4 installation as developer

To install it as developper, first install shadow4 as developper:
```
git clone  https://github.com/oasys-kit/shadow4
cd shadow4
```
Then link the source code to your Oasys python (note that you must use the python that Oasys uses):  
```
python -m pip install -e . --no-deps --no-binary :all:
```
Then, do the same for the OASYS1-shadow4 package: 
```
git clone  https://github.com/oasys-kit/OASYS1-shadow4
cd OASYS1-shadow4
python -m pip install -e . --no-deps --no-binary :all:
```
When restarting Oasys, you will see the shadow4 add-on there.


## OASYS1-shadow4 installation as user

Note that installation as user may end in an obsolete version, therefore for alpha testing it is not encouraged to use this option. 

To install the add-on as user: 

+ In the Oasys window, open "Options->Add-ons..."
+ click the button "Add more" and enter "OASYS1-shadow4". You will see a new entry "Shadow" in the add-on list. Check it and click "OK"
+ Restart Oasys.





## 
