def get_cred(cred_name, *args, **kwargs):
    import subprocess
    import base64
    action = '--get'
    argvalue = ''
    if args:
      for arg in args:
        if arg in ['store', 'update', 'delete']:
          action = '--' + arg
      if kwargs:
        for key, value in kwargs.items():
          value = base64.b64encode(value)
          argvalue = '--' + key + ' ' + value
    bash_command = '/path/to/get-cred.py {0} {1} {2}'.format(action, cred_name, argvalue)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if action == '--get':
      return output.strip()
