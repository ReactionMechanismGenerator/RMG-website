
from django.template import RequestContext
from django.shortcuts import render_to_response
from rmgweb.regression_tests.models import RegressionTestJob
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

def index(request):
    """
    The RMG regression tests homepage.
    """
    # TODO: query db for job queue and render
    jobs = RegressionTestJob.objects.all()
    return render_to_response('regression_tests.html',{'jobs': jobs}, context_instance=RequestContext(request))


@ensure_csrf_cookie
def add_job(request):

	if request.method == 'POST':
		rmgpy_branch = request.POST['autocompleteField_py']
		rmgdb_branch = request.POST['autocompleteField_db']
		job = RegressionTestJob.objects.create(rmgpy_branch=rmgpy_branch, rmgdb_branch=rmgdb_branch)
		spawn_test_job(rmgpy_branch, rmgdb_branch)
		return redirect('/regression_tests')
	else:
		return redirect('/regression_tests')


def spawn_test_job(rmgpy_branch, rmgdb_branch):
	
	import subprocess
	import os

	jobs = 'eg1'
	rmg_tests_script = os.path.join(os.environ["RMGTESTS"], 'local_tests', 'exe.sh')
	command = ['bash',
	           rmg_tests_script,
	           rmgpy_branch,
	           rmgdb_branch,
	           jobs]                         
    
	subprocess.Popen(command)