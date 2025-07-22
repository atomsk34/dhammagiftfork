// Requires the following code in the main.js
//
// global.jQueryComplette = $;

// Also add the following to the config.yml
// solrsuggest.html: 7384

function SuggestController() {
	var _this = this;

	var request = {};

	var response = {};

	this.init = function() {
		// Change back to the old behavior of auto-complete
		// http://jqueryui.com/docs/Upgrade_Guide_184#Autocomplete
		jQueryComplette.ui.autocomplete.prototype._renderItem = function(ul, item) {
			return jQueryComplette("<li></li>").data("item.autocomplete", item).append("<a>" + item.label + "</a>").appendTo(ul);
		};

		var req = false;

		jQueryComplette('form[data-suggest]').each(
			function() {
				var $form = jQueryComplette(this);
				if ($form.hasClass('tx-solr-form-inline')) {
					var $resultsAfterElement = $form.find('input.js-solr-q');
				} else {
					var $resultsAfterElement = $form.find('.drop-up-component-close');
				}
				var $searchField = $form.find('input.js-solr-q');
				var resultContainer = jQueryComplette('<div class="autocomplete-container"></div>');
				$resultsAfterElement.after(resultContainer);
				$searchField.autocomplete(
					{
						appendTo: resultContainer,
						source: function(request, response) {
							_this.request = request;
							_this.response = response;
							if (req) {
								req.abort();
								response();
							}

							req = jQueryComplette.ajax(
								{
									url: $form.data('suggest'),
									dataType: 'jsonp',
									jsonp: "tx_solr[callback]",
									data: {
										tx_solr: {
											queryString: request.term
										}
									},
									success: _this.handleSuggestResponse
								}
							);
						},
						select: function(event, ui) {
							this.value = ui.item.value;
							$form.submit();
						},
						delay: 0,
						minLength: 3
					}
				);
			}
		);
	};

	this.handleSuggestResponse = function(data) {
		req = false;
		var output = [];

		if (!data.suggestions) {
			_this.response(output);
			return;
		}

		jQueryComplette.each(
			data.suggestions, function(key, value) {
				output.push(
					{
						label: key.replace(
							new RegExp(
								'(?![^&;]+;)(?!<[^<>]*)(' +
								jQueryComplette.ui.autocomplete.escapeRegex(_this.request.term) +
								')(?![^<>]*>)(?![^&;]+;)', 'gi'
							), '<strong>$1</strong>'
						),
						value: key
					}
				);
			}
		);

		_this.response(output);
	};
}

jQueryComplette(document).ready(
	function() {
		var solrSuggestController = new SuggestController();
		solrSuggestController.init();

		jQueryComplette('body').on(
			'tx_solr_updated', function() {
				solrSuggestController.init();
			}
		);
	}
);
