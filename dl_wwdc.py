# -*- coding: utf-8 -*-
# execute this script, if you want to start download wwdc video and pdf from the very begin

import os
import wwdc
import dl_wwdc_files



if __name__ == '__main__':
    os.system("python wwdc.py")
    os.system("python dl_wwdc_files.py")