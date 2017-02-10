  angular
      .module('branch_selector', ['ngMaterial', 'ngMessages'])
      .service('github_connector', function($http) {
            this.retrieveRMGrepoBranches = function (repo) {
                return $http.get('https://api.github.com/repos/ReactionMechanismGenerator/'.concat(repo, '/branches'))
                .then(function(response) {
                      return response.data.map(function (branch) {
                                                return {value: branch['name'],
                                                  display: branch['name']};
                                              });
                      });
            };
        })
      .controller('BranchSelectorController', BranchSelectorController)
      .config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{/{');
    $interpolateProvider.endSymbol('}/}');
  });
  
  function BranchSelectorController ($timeout, $q, github_connector, $log) {

    var self = this;
    // list of `state` value/display objects    

    github_connector.retrieveRMGrepoBranches('RMG-Py')
                    .then(function(data){
                        self.branches_rmgpy = data;
                    });

    github_connector.retrieveRMGrepoBranches('RMG-database')
                    .then(function(data){
                        self.branches_rmgdb = data;

                    });
    
    self.selected_branch_rmgpy  = null;
    self.search_text_rmgpy    = null;
    self.selected_branch_rmgdb  = null;
    self.search_text_rmgdb    = null;
    self.querySearch   = querySearch;
    
    // ******************************
    // Internal methods
    // ******************************
    /**
     * Search for branches... use $timeout to simulate
     * remote dataservice call.
     */
    function querySearch (query, branches) {
      var results = query ? branches.filter( createFilterFor(query) ) : branches;
      var deferred = $q.defer();
      $timeout(function () { deferred.resolve( results ); }, Math.random() * 1000, false);
      return deferred.promise;
    }

    /**
     * Create filter function for a query string
     */
    function createFilterFor(query) {
      var lowercaseQuery = angular.lowercase(query);
      return function filterFn(branch) {
        return (branch.value.indexOf(lowercaseQuery) === 0);
      };
    }
  }