#!/usr/bin/python
try:
  import pexpect,re, time
except ImportError,err:
  raise ImportError(str(err) + """:A Critical module is not found""")

class Switch(pexpect.spawn):
   switchCompany = 'juniper'

   def login(self,name,user,passwd):
       self.name = name
       self.user = user
       self.passwd = passwd

       self.send('\r')
       try:
         self.pattern = self.expect(['login:', self.user+'.*%', self.user+'.*>',
                                     self.user+'.*#', 'being used.*option :',
                                     'Username:'])
       except pexpect.TIMEOUT, pexpect.EOF:
             print '\nFailed to connect to device ', self.name
             print '\n\n', sys.exc_info()
             return False

       print '\n ====== Logged into the switch ', self.name, ' ======='
       print '\n ====== Switching to configuration mode ======'

       if (self.pattern <= 3):
           if (self.getToConfigMode()):
               print '\n ======= Switch is in configuration mode ======'
           else:
               print '\n ====== ERROR:: Failed to enter the configuration mode ======'
               return False

       elif (self.pattern == 4):
           self.sendline('1')
           self.pattern = self.expect (['login:', self.user+'.*%', self.user+'.*>', self.user+'.*#'])
           if (self.getToConfigMode()):
               print '\n ======= Switch is in configuration mode ======'
           else:
               print '\n ====== ERROR:: Failed to enter the configuration mode ======'
               return False

       elif (self.pattern == 5):
           try:
             self.sendline(self.user)
             self.expect('word:')
             self.sendline(self.passwd)
             ptrn = self.expect(['>$','#$'])
             if (ptrn == 0):
               self.sendline('enable')
               ptrn = self.expect(['word:','#$'])
               if (ptrn == 0):
                  self.sendline(self.passwd)
                  self.expect('#$')
           except TIMEOUT,EOF:
               print '\nFailed to switch to configuration mode'
               return False
              
       else:
           print "\nNo Pattern Matched"

       return True

   def getSwitchOS(self):
       self.sendline('run show version | grep boot')
       ptrn = self.expect(['JUNOS','Invalid input'])
       #self.sendline()
       #self.expect('edit')
       if (ptrn == 0):
          return 'junos'
       elif (ptrn == 1):
          return 'ios'
       else:
          return False

   def config(self,cmd):
       self.cmd = cmd
       try:	
         self.sendline('commit')  
         pattern=self.expect(['failed', 'complete'])
	 if (pattern == 0):
	   print "\n ======= Doing Rollback since earlier commits failed ======"
           self.sendline('rollback 0')
           self.expect('complete') 
       except pexpect.TIMEOUT, pexpect.EOF:
           print '\n ====== ERROR:: Failed to perform Rollback ======'
           return False
       self.sendline(self.cmd)
       ptrn = self.expect([self.user + '.*#','config.*#'])
       if (ptrn == 0):
         if (re.search('syntax error', self.before + self.after)):
            print '\nSyntax error in the configuration'
            return False
         elif (re.search('\^', self.before + self.after)):
            print '\nError with the configuration command'
            return False
         else:
            print '\n ====== Configuration is Accepted...Doing Configuration Commit Now ====== '
         try:
            self.sendline('commit')
            self.expect('succeeds')
            ptrn = 'succeeds.*complete.*' + self.user + '.*#'
            if (re.search(ptrn,self.before+self.after),re.M|re.S):
               pass
            else:
               return False
         except pexpect.TIMEOUT, pexpect.EOF:
            print '\n**********Failed to commit the configuration**********\n'
            print '***********************ERROR**************************'
            print self.before, self.after
            print '******************************************************'
            return False

       elif (ptrn == 1):
         if (re.search('Invalid input', self.before + self.after)):
            print '\n**********Failed to commit the configuration**********\n'
            print '***********************ERROR**************************'
            print self.before, self.after
            print '******************************************************'
            return False
         else:
               print 'Configuration is committed successfully'
       else:
         print '\n**********Failed to commit the configuration**********\n'
         print '***********************ERROR**************************'
         print self.before, self.after
         print '******************************************************'
         return False

         
       return True

   def disconnect(self):
       try:
         self.close()
       except:
         print '\n ====== ERROR:: Failed to disconnect from device', self.name, ' ======'
         print '\n\n', sys.exc_info()
         return False

       return True
 
   def getToConfigMode(self):
       try: 
         if (self.pattern == 0):
            self.sendline(self.user)
            self.expect('word:')
            self.sendline(self.passwd)
            ptrn = self.expect([self.user + '.*%', self.user + '.*>'])
            if (ptrn == 0):
               self.sendline('cli')
               self.expect(self.user + '.*>')
            self.sendline('edit')
            self.expect('.*#')
         elif (self.pattern == 1):
            self.sendline('cli')
            self.expect(self.user + '.*>')
            self.sendline('edit')
            self.expect(self.user + '.*#')
         elif (self.pattern == 2):
            self.sendline('edit')
            self.expect(self.user + '.*#')
	    print "prininting after getting into config mode", self.before
         elif (self.pattern == 3):
            print "\nAlready in configuration mode"
       except pexpect.TIMEOUT, pexpect.EOF:
            print '\nFailed to switch to configuration mode'
            print self.before, self.after
            return False

       return True
       

