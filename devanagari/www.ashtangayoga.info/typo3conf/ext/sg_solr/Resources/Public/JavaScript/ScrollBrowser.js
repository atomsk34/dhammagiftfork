var SgSolr = SgSolr || {};

/**
 * Initializes the class members and adds the necessary scroll events
 */
SgSolr.SolrScrollBrowser = function() {
	jQuery('.tx-solr .pagination').css('display', 'none');
	this.loadTrigger = jQuery('.tx-solr .results-entry :last');
	this.loadIndicator = jQuery('#tx-solr-search-load');

	if (this.loadTrigger.length) {
		jQuery(document).scroll(this.checkPosition.bind(this));
		this.checkPosition();
		this.resultList = jQuery('.tx-solr .results-list');
	}
};

/**
 * Scroll Browser for Solr
 */
SgSolr.SolrScrollBrowser.prototype = {
	/**
	 * @var {int}
	 */
	lastPage: 1,

	/**
	 * @var {boolean}
	 */
	lock: false,

	/**
	 * @var {JQuery}
	 */
	resultList: null,

	/**
	 * @var {JQuery}
	 */
	loadIndicator: null,

	/**
	 * @var {JQuery}
	 */
	loadTrigger: null,

	/**
	 * @var {string}
	 */
	baseUrl: '',

	/**
	 * Checks the current position of the scrollbar in relation to the
	 * position of the load indicator.
	 *
	 * @return {void}
	 */
	checkPosition: function() {
		if (this.lock || !jQuery('.tx-solr .pagination').length) {
			return;
		}

		var loadTriggerPosition = jQuery('.tx-solr .results-entry :last').position(),
			windowScrollPosition = jQuery(document).scrollTop();

		if (windowScrollPosition > (loadTriggerPosition.top - 1500)) {
			this.loadNextPage();
		}
	},

	/**
	 * Loads the next page of the search results and includes the content
	 * into the existing list.
	 *
	 * @return {void}
	 */
	loadNextPage: function() {
		this.lock = true;

		jQuery.ajax(
			{
				url: location.search,
				data: {
					'tx_solr[page]': (++this.lastPage)
				},

				beforeSend: function() {
					this.loadIndicator.show();
				}.bind(this),

				error: function() {
					this.loadIndicator.hide();
					jQuery('.tx-solr .pagination:last-child').css('display', 'block');
				}.bind(this),

				success: function(response) {
					if (response === '') {
						return;
					}

					var results = jQuery(response).find('.results-list .results-entry');
					if (results.length > 1) {
						this.resultList.append(results);
						this.lock = false;
					}

					this.loadIndicator.css('display', 'none');
				}.bind(this)
			}
		);
	},

	/**
	 * Returns the url query and checks if the search term is set. If not it will be set with the search box value.
	 *
	 * @returns {string}
	 */
	getUrlQuery: function() {
		var queryString = location.search;
		if (queryString.indexOf('q=') > 0) {
			return queryString;
		}

		var $mainSearchInput = jQuery('#tx-solr-search-form-pi-results input.js-solr-q');
		if ($mainSearchInput.length <= 0) {
			return queryString;
		}

		var searchTerm = $mainSearchInput.val();
		if (searchTerm.length <= 0) {
			return queryString;
		}

		if (queryString.indexOf('?') >= 0) {
			return queryString + '&q=' + encodeURIComponent(searchTerm);
		} else {
			return '?q=' + encodeURIComponent(searchTerm);
		}
	}
};

jQuery(document).ready(
	function() {
		(new SgSolr.SolrScrollBrowser());
	}
);
