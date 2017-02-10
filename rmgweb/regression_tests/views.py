
from django.template import RequestContext
from django.shortcuts import render_to_response
from rmgweb.regression_tests.models import RegressionTestJob
from django.shortcuts import redirect

def index(request):
    """
    The RMG regression tests homepage.
    """
    # TODO: query db for job queue and render
    jobs = RegressionTestJob.objects.all()
    return render_to_response('regression_tests.html',{'jobs': jobs}, context_instance=RequestContext(request))


def add_job(request):

	if request.method == 'POST':
		rmgpy_branch = request.POST['autocompleteField_py']
		rmgdb_branch = request.POST['autocompleteField_db']
		job = RegressionTestJob.objects.create(rmgpy_branch=rmgpy_branch, rmgdb_branch=rmgdb_branch)
		return redirect('/regression_tests')
	else:
		return redirect('/regression_tests')