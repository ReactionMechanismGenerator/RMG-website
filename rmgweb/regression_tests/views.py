
from django.template import RequestContext
from django.shortcuts import render_to_response
from rmgweb.regression_tests.models import RegressionTestJob
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
import os

#Used to determine where to look for the file containing job results
FILE_LOCATION = os.getcwd()+'/rmgweb/regression_tests/'

#these are the keywords used to denote a complete file or complete installation
TEST_COMPLETE = 'TEST JOB COMPLETE'
INST_COMPLETE = 'INSTALLATION COMPLETE'
FILE_CRASHED = 'FILE WRITING COMPLETE'

#this is the number of seconds between each checking of the file.
CHECK_FREQ = 5

def index(request):
    """
    The RMG regression tests homepage.
    """
    # TODO: query db for job queue and render
    jobs = RegressionTestJob.objects.all()[::-1][:10]
    return render_to_response('regression_tests.html',{'jobs': jobs}, context_instance=RequestContext(request))



@ensure_csrf_cookie
def add_job(request):
    if request.method == 'POST':
        rmgpy_branch = request.POST['autocompleteField_py']
        rmgdb_branch = request.POST['autocompleteField_db']
        job = RegressionTestJob.objects.create(rmgpy_branch=rmgpy_branch, rmgdb_branch=rmgdb_branch)
        job.job_status = 'wait'
        job.save()
        spawn_test_job(rmgpy_branch, rmgdb_branch, job)
        return redirect('/regression_tests')
    else:
        return redirect('/regression_tests')

def check_job_status(request,job_id):
    from django.http import HttpResponse
    job = RegressionTestJob.objects.get(id=int(job_id))
    return HttpResponse(job.job_status)

def spawn_test_job(rmgpy_branch, rmgdb_branch, job):
    import subprocess
    import os
    import threading

    jobs = 'eg1'
    rmg_tests_script = os.path.join(os.environ["RMGTESTS"], 'local_tests', 'submit_serial.sl')
    command = ['bash',
    rmg_tests_script]

    subprocess.Popen(command)

    search_thread = threading.Timer(CHECK_FREQ,check_for_task_completion,['main_log.out',job])
    search_thread.start()

def check_for_task_completion(file_name, job):
    import threading

    #gets all lines from the file
    example_file = open(file_name,'r')
    file_log = example_file.readlines()
    example_file.close()

    #looks at the lines to see if the INST_COMPLETE keyword in them
    print('WAITING FOR COMPLETION...')
    for line in file_log:
        #if so, the method will search for the file and see if it crashed or succeeded
        if INST_COMPLETE in line:
            print('FILE COMPLETE')
            check_for_file_completion('main_log.out', job)
            return

    #if the keyword was not found a new thread is created to continue the search
    threading.Timer(CHECK_FREQ,check_for_task_completion,[file_name,job]).start()

def check_for_file_completion(file_name, job):
    import subprocess
    import os
    import threading

    print('SEARCHING...')

    #gets all lines in file
    example_file = open(file_name,'r')
    file_log = example_file.readlines()[::-1]
    example_file.close()

    #checks to see if any line in the file contains the TEST_COMPLETE keyword
    for line in file_log:
        #if so, job_status is updated and a message is printed to the console
        if TEST_COMPLETE in line:
            test_name = line.split(':')[0]
            job.job_status = 'done'
            job.save()
            print(test_name+ '-SUCCESSFUL')
            return

    #if the TEST_COMPLETE keyword is not found, the file has crashed and job_status is updated
    if FILE_CRASHED in file_log[0]:
        job.job_status = 'crash'
        job.save()
        print('FILE CRASHED')
        return
    threading.Timer(CHECK_FREQ,check_for_file_completion,[file_name,job]).start()

#checks server output and returns true if still running
def check_if_still_running(job):
    import subprocess

    file_name = 'queue.txt'

    args = ['squeue','>',file_name]
    subprocess.Popen(args)

    queue_file = open(file_name,'r')
    file_log = example_file.readlines()
    queue_file.close()

    #will look for the job and see if it is still in there
    for line in file_log:
        if job in line:
            return True

    return False
