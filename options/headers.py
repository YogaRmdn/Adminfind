import os
import platform
from options.colors import *

def clean_screen():
    os.system("cls" if platform.system() == "nt" else "clear")

def header_tools():
    print(f"""{b_y}
                                                          
     .oo      8          o          ooooo  o            8 
    .P 8      8                     8                   8 
   .P  8 .oPYo8 ooYoYo. o8 odYo.   o8oo   o8 odYo. .oPYo8 
  oPooo8 8    8 8' 8  8  8 8' `8    8      8 8' `8 8    8 
 .P    8 8    8 8  8  8  8 8   8    8      8 8   8 8    8 
.P     8 `YooP' 8  8  8  8 8   8    8      8 8   8 `YooP' {b_r}
..:::::..:.....:..:..:..:....::..:::..:::::....::..:.....:
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                    {b_w}Created By Bang Yog{rs}

""")