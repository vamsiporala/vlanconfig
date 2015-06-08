#!/usr/bin/python

# Importing requrired modules
try:
  import os,re,PsSwitch,sys,argparse
except ImportError, err:
  raise ImportError(str(err) + """:A Critical module is not found""")


# Procedure to fetch the switch details from the config file
def getSwitchInfo(switch,switchFile):
  deviceInfo = {}

  try:
    with open(switchFile) as fd:
      fileop = fd.read()
      compile_str = str(switch) + '\s*' + '({.*?})'
      compile_obj = re.compile(compile_str,re.S|re.I)
      device_match = compile_obj.search(fileop)
      if device_match is None:
         print '\n ======= ERROR:: Failed to find the switch', switch ,'in Admin Switch Database ======\n'
         print ' Kindly Check with your Lab Administrator regarding this Error\n'
         return False
      else:
         device_str = device_match.group(1)
         device_items = device_str.split('\n')
         for i in device_items:
           if re.search(r'=', i):
              j = i.split('=')
              key = j[0].strip('\t').strip()
              val = j[1].strip('\t').strip()
              deviceInfo[key] = val
  except:
     print '\n ======= ERROR:: Failed to contact Admin Switch Database ====== \n'
     print ' Please check with your Lab Administrator regarding this Error\n'
     return False

  return deviceInfo

 
# Procedure to fetch the command line parameters
def fetchArgs():
  parser = argparse.ArgumentParser(description='Provide mandatory command line input arguments')
  
  parser.add_argument('-sw', help = "Switch Name", type=str,required=True)
  parser.add_argument('-int', help = '''Switch Interface
                                           Format : ge-0/0/0 for Juniper Switch
                                                    g0/0/1 for Cisco Switch''', type=str, required=True)
  parser.add_argument('-vlan', help = "VLAN or VLAN list seperated by space", type=int,
                      nargs='+', required=True)
  parser.add_argument('-port_mode', help = "Switch Port Mode access or trunk", type=str, required=False,
                      choices = ['access','trunk'], default = 'access')

  return parser.parse_args()

# Fetch the command line arguments
try:
  args = fetchArgs()
except:
  print '\n ====== INFO:: Please provide required inputs to the tool ====== \n'
  sys.exit()

# Validate the switch port mode and vlan range
if (args.port_mode == 'access') and (len(args.vlan) > 1):
    print '\nMultiple VLANs are NOT allowed for access port mode....'
    print '\nPlease input EITHER port mode to trunk OR only one vlan id'''
    sys.exit()

for vlan in args.vlan:
    if vlan < 1 or vlan > 4095:
      print '\nInvalid vlan specified', vlan, '...Please retry with valid vlan id\n'
      sys.exit()

#Proceed to the configuration
switchFile = '/root/sw-db/sw-db'

if os.path.isfile(switchFile):
     pass
else:
  print '\n ====== ERROR:: Switch Details File is Missing ======\n'
  print ' Please report this Error to your Lab Adminstrator\n'
  sys.exit()
     
# Fetch the switch information and proceed with configuration
try:
  switchInfo = getSwitchInfo(args.sw,switchFile)
  if switchInfo is 0:
     sys.exit()
  else:
     connStr = 'telnet ' + switchInfo['hostname']
     labSwitch = PsSwitch.Switch(connStr)
     if (labSwitch.login(args.sw,switchInfo['username'],switchInfo['password'])):
        if (labSwitch.getSwitchOS() == 'junos'):
           if (args.port_mode == 'trunk'):
               trunkStr = 'port-mode trunk'
           else:
               trunkStr = 'port-mode access'
           cmd = '''delete interface {0}
		set interfaces {0} enable
                set interfaces {0} unit 0 family ethernet-switching {1} vlan members {2}'''.format(args.int, trunkStr, args.vlan)
        elif (labSwitch.getSwitchOS() == 'ios'):
           if (args.port_mode == 'trunk'):
               trunkStr = 'allowed'
           else:
               trunkStr = ''
           cmd = '''config terminal
                    interface {0}
                    switchport mode {1}
                    switchport {1} {2} vlan {3}
                    end'''.format(args.int,args.port_mode,trunkStr,args.vlan)
        else:
           print '\n ====== ERROR:: Failed to find the Lab Switch OS...Hence Aborting ======'
            
        print "\n ====== Configuring the vlan", args.vlan, "under interface", args.int, \
                         "on switch", args.sw, " ====== \n" 
        if (labSwitch.config(cmd)):
           print '\n ====== SUCCESS:: Vlan is configured successfully ======'
        else:
           print '\n ====== ERROR:: Failed to configure the vlan ======'
    
        if (labSwitch.disconnect()):
            print '\n ======= Logged out of switch ======'
        else:
            print '\n ====== ERROR:: Failed to logout of switch ======'

except:
   sys.exit()
