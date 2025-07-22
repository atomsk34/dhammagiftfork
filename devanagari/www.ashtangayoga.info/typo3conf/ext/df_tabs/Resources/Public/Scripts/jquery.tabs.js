/**
 * Initializes the tab widget
 *
 * @param {string} menuEntries
 * @param {string} contentEntries
 * @param {object} options
 * @return {void}
 */
var TabBar = function(menuEntries, contentEntries, options) {
	/**
	 * Available options
	 *
	 * startIndex: starting tab index (beginning at 0)
	 * enableAutoPlay: usage of an auto play mechanism to switch between tabs
	 * autoPlayInterval: the time gap between the switch between two slides
	 * enableMouseOver: usage of mouse over in addition the normal click event for changing a tab
	 * classPrefix: prefix for all assigned classes
	 * hashName: prefix for the location hash listener
	 * pollingInterval: location hash polling interval
	 * animateCallback: animation callback function
	 *
	 * Events:
	 * onBeforeInitialize
	 * onAfterInitialize
	 * onTabChange
	 *
	 * @cfg {Object}
	 */
	this.options = {
		startIndex: 0,
		enableAutoPlay: false,
		autoPlayInterval: 7000,
		enableMouseOver: false,
		classPrefix: 'tx-dftabs-',
		hashName: 'tab',
		pollingInterval: 1000,
		animationCallback: null,

		onBeforeInitialize: null,
		onAfterInitialize: null,
		onTabChange: null,
		changeHashOnTabChange: false
	};
	$.extend(this.options, options);

	/**
	 * Tab Entry Array with Fields of Type "Object"
	 *
	 * Structure:
	 * menuItem: related menu element
	 * contentItem: related content element
	 *
	 * @type {Array}
	 */
	this.elementMap = [];

	/**
	 * The Active Tab
	 *
	 * @type {int}
	 */
	this.previousTab = this.options.startIndex;

	/**
	 * The AutoPlay Instance
	 *
	 * @type {int}
	 */
	this.autoPlay = 0;

	/**
	 * Timed Display Method
	 *
	 * @type {int}
	 */
	this.timedDisplayFunction = 0;

	for (var i = 0; i < menuEntries.length; ++i) {
		this.elementMap[i] = {};
		this.elementMap[i].menuItem = $(menuEntries[i]);
		this.elementMap[i].contentItem = $(contentEntries[i]);
	}

	this.finalizeInitialisation();
};

/**
 * A tab-bar widget with very basic functionality
 *
 * @author Stefan Galinski <stefan.galinski@gmail.com>
 */
TabBar.prototype = {
	/**
	 * Finalizes the initialisation
	 *
	 * @return {void}
	 */
	finalizeInitialisation: function() {
		this.trigger('beforeInitialize', this);

		this.previousTab = this.options.startIndex;
		this.parseContentLinks().addEvents().initAutoPlay().addLocationHashPolling();

		this.trigger('afterInitialize', this);
	},

	/**
	 * Parses all links and adds a smooth scrolling to the tab if the link
	 * references to an internal tab on the very same page
	 *
	 * @return {TabBar}
	 */
	parseContentLinks: function() {
		$.each(this.elementMap, function(index, element) {
			var links = element.contentItem.find('a');
			links.each(function(index, link) {
				var parts = link.href.split('#');
				if (parts[1] && parts[1].substr(this.options.hashName.length) === this.options.hashName
					&& parts[0] === location.href.split('#')[0]) {
					var hashIndex = parts[1].substr(this.options.hashName.length);
					$(link).click(this.scrollToTab.bind(this, hashIndex));
				}
			}.bind(this));
		}.bind(this));

		return this;
	},

	/**
	 * Scrolls to the menu item of the given tab index
	 *
	 * @param {int} tabIndex
	 * @return {void}
	 */
	scrollToTab: function(tabIndex) {
		$(window).scrollTop(this.elementMap[tabIndex].menuItem.offset().y);
	},

	/**
	 * Adds the requested events to the tab menu elements
	 *
	 * @return {TabBar}
	 */
	addEvents: function() {
		$.each(this.elementMap, function(index, element) {
			if (this.options.enableMouseOver) {
				element.menuItem.mouseenter(this.timedDisplay.bind(this, index));
				element.contentItem.mouseenter(this.clearTimedDisplay.bind(this));
			} else {
				element.menuItem.click(function(event) {
					event.preventDefault();
					this.display.call(this, index)
				}.bind(this));
			}

			if (this.options.enableAutoPlay) {
				if (this.options.enableMouseOver) {
					element.menuItem.mouseenter(this.stopAutoPlay.bind(this));
					element.menuItem.mouseleave(this.startAutoPlay.bind(this));
					element.menuItem.click(this.startAutoPlay.bind(this));
				} else {
					element.menuItem.click(this.stopAutoPlay.bind(this));
				}
			}
		}.bind(this));

		return this;
	},

	/**
	 * Initializes the autoplay mechanism based on the visibility state
	 *
	 * Note: If the visibility state isn't available, the autoplay functionality is
	 * started directly.
	 *
	 * @return {TabBar}
	 */
	initAutoPlay: function() {
		var hidden = null,
			visibilityChange = null;
		if (typeof document.hidden !== 'undefined') {
			hidden = 'hidden';
			visibilityChange = 'visibilitychange';
		} else if (typeof document.mozHidden !== 'undefined') {
			hidden = 'mozHidden';
			visibilityChange = 'mozvisibilitychange';
		} else if (typeof document.msHidden !== 'undefined') {
			hidden = 'msHidden';
			visibilityChange = 'msvisibilitychange';
		} else if (typeof document.webkitHidden !== 'undefined') {
			hidden = 'webkitHidden';
			visibilityChange = 'webkitvisibilitychange';
		}

		if (visibilityChange) {
			document.addEventListener(
				visibilityChange, this.toggleAutoplayBasedOnVisibility.bind(this, [hidden]), false
			);
			this.toggleAutoplayBasedOnVisibility(hidden);
		} else {
			this.startAutoPlay();
		}

		return this;
	},

	/**
	 * Adds an URL hash evaluation with a polling interval of 1000ms to grant the possibility to
	 * manually open content elements by changing the location hash inside the URL (e.g. acc123).
	 *
	 * @return {void}
	 */
	addLocationHashPolling: function() {
		setTimeout(this.hashHandler.bind(this), 1);
		setInterval(this.hashHandler.bind(this), 100);
	},

	/**
	 * Location Hash Handler
	 *
	 * @return {void}
	 */
	hashHandler: function() {
		if (this.locationHash === window.location.hash) {
			return;
		}

		var index = -1;
		this.locationHash = window.location.hash;
		if (this.locationHash !== '') {
			var matchExpression = new RegExp(this.options.hashName + '(\\d+)', 'i');
			var matchResult = matchExpression.exec(this.locationHash);
			index = parseInt(matchResult ? matchResult[1] : '', 10);
			if (index >= 0 && index < this.elementMap.length) {
				this.display(index, false);
			}
		} else {
			if (this.previousTab !== this.options.startIndex) {
				this.display(this.options.startIndex, false);
			}
		}
	},

	/**
	 * Adds a small delay before displaying a tab (useful for mouseover)
	 *
	 * Note: The delay method is saved in the class property "timedDisplayFunction".
	 *
	 * @param {int} nextTabIndex
	 * @return {TabBar}
	 */
	timedDisplay: function(nextTabIndex) {
		this.clearTimedDisplay();
		this.timedDisplayFunction = setTimeout(this.display.bind(this, nextTabIndex), 250);

		return this;
	},

	/**
	 * Clears the timed display function
	 *
	 * @return {TabBar}
	 */
	clearTimedDisplay: function() {
		clearTimeout(this.timedDisplayFunction);

		return this;
	},

	/**
	 * Displays the given tab index
	 *
	 * @param {int} nextTabIndex
	 * @param {Boolean} triggeredByAutoPlay
	 * @return {TabBar}
	 */
	display: function(nextTabIndex, triggeredByAutoPlay) {
		if (triggeredByAutoPlay !== true) {
			triggeredByAutoPlay = false;
		}

		nextTabIndex = parseInt(nextTabIndex, 10);
		var tabIndexInRange = nextTabIndex >= 0 && nextTabIndex < this.elementMap.length;
		if (isNaN(nextTabIndex) || this.previousTab === nextTabIndex || !tabIndexInRange) {
			return this;
		}

		if (this.options.animationCallback) {
			this.options.animationCallback.call(this, nextTabIndex, triggeredByAutoPlay);
		} else {
			this.animate(nextTabIndex);
		}

		this.trigger('tabChange', this, this.previousTab, nextTabIndex);

		if (this.options.changeHashOnTabChange) {
			// save current scroll position in order to apply it after hash changed
			// this prevents the content from jumping around as the tabs change
			var currentScrollY = window.scrollY;
			window.location.hash = this.options.hashName + nextTabIndex;
			window.scrollTo(0, currentScrollY);
		}

		return this;
	},

	/**
	 * Default "animation" of the transition between two tabs. In real it's just
	 * a toggling of the selected classes for the content and menu items. Define
	 * your own animation function to get a nice effect.
	 *
	 * @param {int} nextTabIndex
	 * @return {TabBar}
	 */
	animate: function(nextTabIndex) {
		this.toggleContentItemSelectionClasses(nextTabIndex);
		this.toggleMenuEntrySelectionClasses(nextTabIndex);
		this.previousTab = nextTabIndex;

		return this;
	},

	/**
	 * Toggles the "tabContentSelected" class on the last and current content elements
	 *
	 * @param {int} nextTabIndex
	 * @return {TabBar}
	 */
	toggleContentItemSelectionClasses: function(nextTabIndex) {
		var selectedClass = this.options.classPrefix + 'tabContentSelected';
		this.elementMap[this.previousTab].contentItem.removeClass(selectedClass);
		this.elementMap[nextTabIndex].contentItem.addClass(selectedClass);

		return this;
	},

	/**
	 * Toggles the "tabMenuEntrySelected" class on the last and current menu entries
	 *
	 * @param {int} nextTabIndex
	 * @return {TabBar}
	 */
	toggleMenuEntrySelectionClasses: function(nextTabIndex) {
		var selectedClass = this.options.classPrefix + 'tabMenuEntrySelected';
		this.elementMap[nextTabIndex].menuItem.addClass(selectedClass);
		this.elementMap[this.previousTab].menuItem.removeClass(selectedClass);

		return this;
	},

	/**
	 * Toggles the autplay setting based on the visibility state of the page
	 *
	 * @param {string} hidden field with the hidden state in the document object
	 * @return {TabBar}
	 */
	toggleAutoplayBasedOnVisibility: function(hidden) {
		if (!document[hidden]) {
			this.startAutoPlay();
		} else {
			this.stopAutoPlay();
		}

		return this;
	},

	/**
	 * Implements the auto-play mechanism
	 *
	 * @return {void}
	 */
	autoPlayMechanism: function() {
		if (this.previousTab < this.elementMap.length - 1) {
			this.display(this.previousTab + 1, true);
		} else {
			this.display(0, true);
		}
	},

	/**
	 * Starts the auto-play mechanism
	 *
	 * @return {TabBar}
	 */
	startAutoPlay: function() {
		if (this.options.enableAutoPlay && !this.autoPlay) {
			this.autoPlay = setInterval(this.autoPlayMechanism.bind(this), this.options.autoPlayInterval);
		}

		return this;
	},

	/**
	 * Stops the auto-play mechanism
	 *
	 * @return {TabBar}
	 */
	stopAutoPlay: function() {
		clearInterval(this.autoPlay);
		this.autoPlay = 0;

		return this;
	},

	/**
	 * Triggers an event
	 *
	 * @return {void}
	 */
	trigger: function(event) {
		var onFunction = 'on' + event.charAt(0).toUpperCase() + event.slice(1);
		if (typeof this.options[onFunction] === 'function') {
			var args = Array.prototype.slice.call(arguments);
			args.shift();
			this.options[onFunction].call(this, args[0], args[1], args[2], args[3]);
		}
	}
};
