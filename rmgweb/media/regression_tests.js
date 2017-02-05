  angular
      .module('branch_selector', ['ngMaterial', 'ngMessages'])
      .controller('BranchSelectorController', BranchSelectorController)
      .config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{/{');
    $interpolateProvider.endSymbol('}/}');
  });
  
  function BranchSelectorController ($timeout, $q) {
    var self = this;
    // list of `state` value/display objects
    self.branches_rmgpy        = load_rmgpy_branches();
    self.selected_branch_rmgpy  = null;
    self.search_text_rmgpy    = null;
    self.branches_rmgdb        = load_rmgdb_branches();
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
     * Build `branches` list of key/value pairs
     */
    function load_rmgpy_branches() {
      var allBranches = 'master, nitrogen, polycyclic';
      return allBranches.split(/, +/g).map( function (branch) {
        return {
          value: branch.toLowerCase(),
          display: branch
        };
      });
    }

    function load_rmgdb_branches() {
      var allBranches = 'master, nitrogen-db, polycyclic-db';
      return allBranches.split(/, +/g).map( function (branch) {
        return {
          value: branch.toLowerCase(),
          display: branch
        };
      });
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