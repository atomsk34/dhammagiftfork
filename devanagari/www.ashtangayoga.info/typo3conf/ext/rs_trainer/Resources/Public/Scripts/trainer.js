var AY = AY || {};

AY.DevanagariTrainer = function() {
	var $rsTrainers = $('.tx-rstrainer');
	if ($rsTrainers.length <= 0) {
		return;
	}

	this.placeHolderImage = AY.Settings.placeholderImage;
	this.arrMessages = [
		AY.Settings.labelSuccess,
		AY.Settings.labelAmountOfErrors,
		AY.Settings.labelAmountOfTips,
		AY.Settings.labelPerfectSuccess
	];
	this.initGame(4);
	this.initialize();
};

AY.myFadeOut = function(element, time, callback) {
	time = time || 200;
	element.animate({opacity: 0}, time, 'swing', function() {
		$(this).css({visibility: 'hidden'});
		if (typeof callback !== 'undefined') {
			callback.call();
		}
	});
};

AY.myFadeIn = function(element, time, callback) {
	time = time || 200;
	element.css({visibility: 'visible'}).animate({opacity: 1}, time, function(){
		if (typeof callback !== 'undefined') {
			callback.call();
		}
	});
};

AY.DevanagariTrainer.prototype = {
	/**
	 * @var {Array}
	 */
	CARDS_PER_LEVEL: [0, 84, 31, 33, 10, 10],

	/**
	 * @var {int}
	 */
	MAX_CARDS_ON_SIDE: 10,

	/**
	 * @var {Array}
	 */
	imageMap: [],

	/**
	 * @var {Array}
	 */
	cardsLeft: [],

	/**
	 * @var {Array}
	 */
	cardsRight: [],

	/**
	 * @var {Array}
	 */
	arrMessages: [],

	/**
	 * @var {int}
	 */
	clickedCardFieldLeft: 0,

	/**
	 * @var {int}
	 */
	clickedCardFieldRight: 0,

	/**
	 * @var {int}
	 */
	totalNumber: 0,

	/**
	 * @var {int}
	 */
	selectionLeft: 0,

	/**
	 * @var {int}
	 */
	selectionRight: 0,

	/**
	 * @var {int}
	 */
	clickCount: 0,

	/**
	 * @var {int]
	 */
	tippCount: 0,

	/**
	 * @var {int}
	 */
	countSuccess: 0,

	/**
	 * @var {int}
	 */
	errorCount: 0,

	/**
	 * @var {int}
	 */
	selectionForCardBrowser: 0,

	/**
	 * @var {boolean}
	 */
	cardBrowserVisible: false,

	/**
	 * @var {String}
	 */
	isFirstClickedRightOrLeft: '',

	/**
	 * @var {String}
	 */
	placeHolderImage: '',

	/**
	 * @var {int}
	 */
	newLeftCard: 0,

	/**
	 * @var {int}
	 */
	newRightCard: 0,

	/**
	 * @var {int}
	 */
	pairsInGameField: 0,

	/**
	 * Add listeners to DOM elements
	 *
	 * @return {void}
	 */
	initialize: function() {
		$('#selLevel').change(function(event) {
			this.initGame(event.target.options.selectedIndex);
		}.bind(this));

		$('#infoBox').click(function(event) {
			event.preventDefault();
			this.showHideGameInfoBox(false);
		}.bind(this));

		$('#helpBox').click(function(event) {
			event.preventDefault();
			this.showHideHelp(false);
		}.bind(this));

		$('#hintBox').click(function(event) {
			event.preventDefault();
			this.quickHelp(this.isFirstClickedRightOrLeft);
		}.bind(this));

		$('#leftPreviousArrowBox').click(function(event) {
			event.preventDefault();
			this.prevCardsLeft();
		}.bind(this));

		$('#leftNextArrowBox').click(function(event) {
			event.preventDefault();
			this.nextCardsLeft();
		}.bind(this));

		$('#rightPreviousArrowBox').click(function(event) {
			event.preventDefault();
			this.prevCardsRight();
		}.bind(this));

		$('#rightNextArrowBox').click(function(event) {
			event.preventDefault();
			this.nextCardsRight();
		}.bind(this));

		$('#newGameBox').click(function(event) {
			event.preventDefault();
			this.initVar();
			this.newGame();
		}.bind(this));

		$('#finishGameBox').click(function(event) {
			event.preventDefault();
			this.finishGame();
		}.bind(this));

		for (var a = 0; a < 10; ++a) {
			var clickTargetLeft = $('#left_href_' + a);
			var clickTargetRight = $('#right_href_' + a);

			clickTargetLeft.click(function(event) {
				event.preventDefault();
				this.setLeft(event.target.id.substring('left_'.length));
			}.bind(this));

			clickTargetLeft.dblclick(function(event) {
				this.quickHelp('left_' + event.target.id.substring('left_'.length));
			}.bind(this));

			clickTargetRight.click(function(event) {
				event.preventDefault();
				this.setRight(event.target.id.substring('right_'.length));
			}.bind(this));

			clickTargetRight.dblclick(function(event) {
				this.quickHelp('right_' + event.target.id.substring('right_'.length));
			}.bind(this));
		}
	},

	/**
	 * Initialize the default game settings
	 *
	 * @param {int} level
	 * @return {void}
	 */
	initGame: function(level) {
		level = parseInt(level, 10);

		var invisibleElementsUntilStarted = $('.rs-trainer-invisibleUntilStarted');
		if (level === 0) {
			AY.myFadeOut(invisibleElementsUntilStarted);
			this.showHideCardTables(level);
			return;
		}

		this.totalNumber = this.CARDS_PER_LEVEL[level];
		AY.myFadeIn(invisibleElementsUntilStarted);
		this.showHideGameInfoBox(true);
		this.showHideCardTables(level - 1);
		this.initVar();
		this.newGame();
	},

	/**
	 * Initialize the variables for a new game
	 * @return {void}
	 */
	initVar: function() {
		this.cardsLeft = [];
		this.cardsRight = [];
		this.clickedCardFieldLeft = 0;
		this.clickedCardFieldRight = 0;
		this.selectionLeft = 0;
		this.selectionRight = 0;
		this.clickCount = 0;
		this.tippCount = 0;
		this.countSuccess = 0;
		this.errorCount = 0;
		this.selectionForCardBrowser = 0;
		this.cardBrowserVisible = false;
		this.isFirstClickedRightOrLeft = '';
		this.newLeftCard = 0;
		this.newRightCard = 0;
		this.pairsInGameField = 0;
		this.cleanHelp();
		$('#totalNumber')[0].innerHTML = this.totalNumber + ' ';
		$('#successNumber')[0].innerHTML = this.countSuccess + ' ';
	},

	/**
	 * Mixes the cards and add these to the card browser
	 *
	 * @return {void}
	 */
	newGame: function() {
		var usedRandomNumbers = [];
		var pairs = 1;
		var cardCounter = 0;
		var doLeft = true;
		var totalNumberMultipliedByTwo = this.totalNumber * 2;

		this.cardBrowserVisible = this.totalNumber > this.MAX_CARDS_ON_SIDE;
		if (this.cardBrowserVisible) {
			this.showCardBrowser();
		} else {
			this.hideCardBrowser();
		}

		for (var i = 0; i < this.totalNumber; ++i) {
			usedRandomNumbers[i] = 3;
		}

		while (cardCounter < totalNumberMultipliedByTwo) {
			var rand = Math.ceil(Math.random() * this.totalNumber) - 1;
			if (doLeft) {
				if (usedRandomNumbers[rand] === 3) {
					this.cardsLeft[this.cardsLeft.length] = rand + this.offsetInImageMap;
					usedRandomNumbers[rand] = 2;
					++cardCounter;
				} else if (usedRandomNumbers[rand] === 1) {
					this.cardsLeft[this.cardsLeft.length] = rand + this.offsetInImageMap;
					usedRandomNumbers[rand] = -1;
					++cardCounter;
					++pairs;
				}
				doLeft = false;
			} else {
				if (usedRandomNumbers[rand] === 3) {
					this.cardsRight[this.cardsRight.length] = rand + this.offsetInImageMap;
					usedRandomNumbers[rand] = 1;
					++cardCounter;
				} else if (usedRandomNumbers[rand] === 2) {
					this.cardsRight[this.cardsRight.length] = rand + this.offsetInImageMap;
					usedRandomNumbers[rand] = -1;
					++cardCounter;
					++pairs;
				}
				doLeft = true;
			}

			while (pairs < cardCounter / 4) {
				rand = Math.ceil(Math.random() * this.totalNumber) - 1;
				if (doLeft) {
					if (usedRandomNumbers[rand] === 2) {
						this.cardsRight[this.cardsRight.length] = rand + this.offsetInImageMap;
						usedRandomNumbers[rand] = -1;
						++cardCounter;
						++pairs;
						doLeft = false;
					}
				} else {
					if (usedRandomNumbers[rand] === 1) {
						this.cardsLeft[this.cardsLeft.length] = rand + this.offsetInImageMap;
						usedRandomNumbers[rand] = -1;
						++cardCounter;
						++pairs;
						doLeft = true;
					}
				}
			}
		}

		for (var m = 0; m < this.MAX_CARDS_ON_SIDE; ++m) {
			this.imgNameLeft = '#left_' + m;
			this.imgNameRight = '#right_' + m;
			$(this.imgNameLeft).attr('src', this.getCardImageUrl('showLeft_', this.cardsLeft[m]));
			$(this.imgNameRight).attr('src', this.getCardImageUrl('showRight_', this.cardsRight[m]));
			AY.myFadeIn($(this.imgNameLeft));
			AY.myFadeIn($(this.imgNameRight));
		}

		this.selectionLeft = this.MAX_CARDS_ON_SIDE;
		this.selectionRight = this.MAX_CARDS_ON_SIDE;

		AY.myFadeOut($('#rs-trainer-resultTables').find('img'), 0);
	},

	/**
	 * Finish the game and reset all variables
	 *
	 * @return {void}
	 */
	finishGame: function() {
		AY.myFadeIn($('#rs-trainer-resultTables').find('img'));

		for (var j = 0; j < this.MAX_CARDS_ON_SIDE; ++j) {
			this.imgNameLeft = '#left_' + j;
			this.imgNameRight = '#right_' + j;
			AY.myFadeOut($(this.imgNameLeft));
			AY.myFadeOut($(this.imgNameRight));
		}
		this.cleanHelp();
		this.removeBorder();
		this.hideCardBrowser();
		this.cardBrowserVisible = false;
	},

	/**
	 * It's the click listener for the left card browser
	 * Controls the help fields and the border for the left card browser,
	 * also calling the checkPair() function, if one card is selected in every card browser
	 *
	 * @param {String} imgCounter
	 * @return {void}
	 */
	setLeft: function(imgCounter) {
		this.removeBorderLeft();
		this.clickedCardFieldLeft = parseInt(imgCounter, 10);
		if (isNaN(this.clickedCardFieldLeft)) {
			return;
		}

		var leftName = 'left_' + imgCounter;
		var leftField = $('#' + leftName);

		leftField[0].className = 'setBorder';
		this.checkCleanHelp();

		var leftHelp = $('#help_left');
		leftHelp.attr('src', leftField.attr('src'));
		AY.myFadeIn(leftHelp);
		++this.clickCount;

		if (this.clickCount === 1) {
			this.isFirstClickedRightOrLeft = leftName;
		}

		if (this.clickCount >= 2) {
			if (this.isFirstClickedRightOrLeft === leftName) {
				this.quickHelp(leftName);
			}

			if (this.isFirstClickedRightOrLeft.substr(0, 4) === leftName.substr(0, 4)) {
				this.clickCount = 1;
				this.removeBorder();
				leftField[0].className = 'setBorder';
				this.cleanHelp();
				leftHelp.attr('src', leftField.attr('src'));
				AY.myFadeIn(leftHelp);
				this.isFirstClickedRightOrLeft = leftName;
			} else {
				this.checkPair();
			}
		}
	},

	/**
	 * It's the click listener for the right card browser
	 * Controls the help fields and the border for the right card browser,
	 * also calling the checkPair() function, if one card is selected in every card browser
	 *
	 * @param {String} imgCounter
	 * @return {void}
	 */
	setRight: function(imgCounter) {
		this.removeBorderRight();
		this.clickedCardFieldRight = parseInt(imgCounter, 10);
		if (isNaN(this.clickedCardFieldRight)) {
			return;
		}

		var rightName = 'right_' + imgCounter;
		var rightField = $('#' + rightName);

		rightField[0].className = 'setBorder';
		this.checkCleanHelp();

		var rightHelp = $('#help_right');
		rightHelp.attr('src', rightField.attr('src'));
		AY.myFadeIn(rightHelp);
		++this.clickCount;

		if (this.clickCount === 1) {
			this.isFirstClickedRightOrLeft = rightName;
		}

		if (this.clickCount >= 2) {
			if (this.isFirstClickedRightOrLeft === rightName) {
				this.quickHelp(rightName);
			}

			if (this.isFirstClickedRightOrLeft.substr(0, 5) === rightName.substr(0, 5)) {
				this.clickCount = 1;
				this.removeBorder();
				rightField[0].className = 'setBorder';
				this.cleanHelp();
				rightHelp.attr('src', rightField.attr('src'));
				AY.myFadeIn(rightHelp);
				this.isFirstClickedRightOrLeft = rightName;
			} else {
				this.checkPair();
			}
		}
	},

	/**
	 * Check which help field should be visible and calling the function deleteTip()
	 *
	 * @param {String} pos
	 * @return {void}
	 */
	quickHelp: function(pos) {
		if (this.clickCount === 1) {
			var posSrc = $('#' + pos).attr('src');
			var leftHelpField = $('#help_left');
			var rightHelpField = $('#help_right');
			if ('left' === pos.substr(0, 4)) {
				leftHelpField.attr('src', posSrc);
				rightHelpField.attr('src', posSrc.replace(/_l/g, '_r'));
				AY.myFadeIn(leftHelpField);
				AY.myFadeIn(rightHelpField);
				setTimeout(this.deleteTip.bind(this, 'help_right'), 3000);
			} else {
				rightHelpField.attr('src', posSrc);
				leftHelpField.attr('src', posSrc.replace(/_r/g, '_l'));
				AY.myFadeIn(rightHelpField);
				AY.myFadeIn(leftHelpField);
				setTimeout(this.deleteTip.bind(this, 'help_left'), 3000);
			}
			++this.tippCount;
		}
	},

	/**
	 * Checks if a pair is correct and count the errors
	 * Also creates a success message, when all pairs found
	 *
	 * @return {void}
	 */
	checkPair: function() {
		var leftName = 'left_' + this.clickedCardFieldLeft;
		var rightName = 'right_' + this.clickedCardFieldRight;
		var leftSelectedImage = parseInt(this.getImageValue(leftName), 10);
		var rightSelectedImage = parseInt(this.getImageValue(rightName), 10);

		if (leftSelectedImage === rightSelectedImage) {
			AY.myFadeIn($('#showLeft_' + leftSelectedImage));
			AY.myFadeIn($('#showRight_' + rightSelectedImage));

			for (var i = 0; i < this.cardsLeft.length; ++i) {
				if (this.cardsLeft[i] === leftSelectedImage) {
					this.cardsLeft.splice(i, 1);
					break;
				}
			}

			for (var j = 0; j < this.cardsRight.length; ++j) {
				if (this.cardsRight[j] === rightSelectedImage) {
					this.cardsRight.splice(j, 1);
					break;
				}
			}

			this.checkSelectionCards();

			if (this.cardBrowserVisible) {
				var leftField = $('#' + leftName);
				var rightField = $('#' + rightName);

				this.changeSelectionLeftCards('+');
				this.selectNewCardLeft(this.getLeftCards());
				leftField.attr('src', this.getCardImageUrl('showLeft_', this.newLeftCard));
				AY.myFadeIn(leftField);

				this.changeSelectionRightCards('+');
				this.selectNewCardRight(this.getRightCards());
				rightField.attr('src', this.getCardImageUrl('showRight_', this.newRightCard));
				AY.myFadeIn(rightField);
			} else {
				AY.myFadeOut($('#' + leftName));
				AY.myFadeOut($('#' + rightName));
			}

			if (this.cardsLeft.length <= this.MAX_CARDS_ON_SIDE) {
				this.cardBrowserVisible = false;
				this.hideCardBrowser();
			}

			this.setHelpSuccess();
			++this.countSuccess;
			$('#successNumber')[0].innerHTML = this.countSuccess + ' ';
		} else {
			++this.errorCount;
			this.setHelpError();

			if (this.clickedCardFieldLeft !== '' && this.clickedCardFieldLeft !== null || leftName === 'left_0') {
				var leftNameSrc = $('#' + leftName).attr('src');
				var leftErrorField = $('#help_left_error');
				var leftHelpField = $('#help_left');

				leftErrorField.attr('src', leftNameSrc);
				AY.myFadeIn(leftErrorField);
				leftHelpField.attr('src', leftNameSrc.replace(/_l/g, '_r'));
				AY.myFadeIn(leftHelpField);
			}

			if (this.clickedCardFieldRight !== '' && this.clickedCardFieldRight !== null || rightName === 'right_0') {
				var rightNameSrc = $('#' + rightName).attr('src');
				var rightErrorField = $('#help_right_error');
				var rightHelpField = $('#help_right');

				rightErrorField.attr('src', rightNameSrc);
				AY.myFadeIn(rightErrorField);
				rightHelpField.attr('src', rightNameSrc.replace(/_r/g, '_l'));
				AY.myFadeIn(rightHelpField);
			}
		}

		this.cleanMemory();

		if (this.countSuccess === this.totalNumber) {
			this.cleanHelp();
			var perfectGame = '';
			if (this.errorCount === 0 && this.tippCount === 0) {
				perfectGame = '\n-------------------------------\n' + this.arrMessages[3];
			}
			alert(this.arrMessages[0] + '\n-------------------------------\n' +
				this.arrMessages[1] + ' ' + this.errorCount + '\n' +
				this.arrMessages[2] + ' ' + this.tippCount + perfectGame);
		}
	},

	/**
	 * Checks the pairs in the game fields
	 *
	 * @return {void}
	 */
	checkPairsInGameField: function() {
		var leftCards = this.getLeftCards();
		var rightCards = this.getRightCards();

		this.pairsInGameField = 0;

		for (var index_left = 0; index_left < leftCards.length; ++index_left) {
			for (var index_right = 0; index_right < rightCards.length; ++index_right) {
				if (leftCards[index_left] === rightCards[index_right]) {
					++this.pairsInGameField;
				}
			}
		}
	},

	/**
	 * Removes pairs from two arrays
	 *
	 * @param {Array} cardsWithPairsLeft
	 * @param {Array} cardsWithPairsRight
	 * @returns {Array}
	 */
	removePairsFromRightCards: function(cardsWithPairsLeft, cardsWithPairsRight) {
		for (var index_left = 0; index_left < cardsWithPairsLeft.length; ++index_left) {
			for (var index_right = 0; index_right < cardsWithPairsRight.length; ++index_right) {
				if (cardsWithPairsLeft[index_left] === cardsWithPairsRight[index_right]) {
					cardsWithPairsRight.splice(index_right, 1);
				}
			}
		}
		return cardsWithPairsRight;
	},

	/**
	 * Select the cards in the left card field
	 *
	 * @return {Array}
	 */
	getLeftCards: function() {
		var selectedCards = [];
		var imgName = 'left_';

		for (var i = 0; i < this.MAX_CARDS_ON_SIDE; ++i) {
			selectedCards[i] = this.getImageValue(imgName + i);
		}
		return selectedCards;
	},

	/**
	 * Select the cards in the right card field
	 *
	 * @return {Array}
	 */
	getRightCards: function() {
		var selectedCards = [];
		var imgName = 'right_';

		for (var i = 0; i < this.MAX_CARDS_ON_SIDE; ++i) {
			selectedCards[i] = this.getImageValue(imgName + i);
		}
		return selectedCards;
	},

	/**
	 * Select a new card for the left card field
	 *
	 * @param {Array} selectedCards
	 * @return {void}
	 */
	selectNewCardLeft: function(selectedCards) {
		this.checkPairsInGameField();

		if (this.pairsInGameField <= 2) {
			var cardsWithoutPairsRight = this.removePairsFromRightCards(this.getLeftCards(), this.getRightCards());
			var rand = Math.ceil(Math.random() * cardsWithoutPairsRight.length) - 1;

			this.newLeftCard = cardsWithoutPairsRight[rand];
		} else {
			this.newLeftCard = this.cardsLeft[this.selectionLeft];
			for (var i = 0; i < this.MAX_CARDS_ON_SIDE; ++i) {
				if (parseInt(selectedCards[i], 10) === this.newLeftCard) {
					this.changeSelectionLeftCards('+');
					this.selectNewCardLeft(selectedCards);
				}
			}
		}
	},

	/**
	 * Select a new card for the right card field
	 *
	 * @param {Array} selectedCards
	 * @return {void}
	 */
	selectNewCardRight: function(selectedCards) {
		this.newRightCard = this.cardsRight[this.selectionRight];
		for (var i = 0; i < this.MAX_CARDS_ON_SIDE; ++i) {
			if (parseInt(selectedCards[i], 10) === this.newRightCard) {
				this.changeSelectionRightCards('+');
				this.selectNewCardRight(selectedCards);
			}
		}
	},

	/**
	 * Shows the next cards in the left card browser
	 *
	 * @return {void}
	 */
	nextCardsLeft: function() {
		for (var k = 0; k < this.MAX_CARDS_ON_SIDE; ++k) {
			this.imgNameLeft = 'left_' + k;
			var leftImgField = $('#' + this.imgNameLeft);

			leftImgField.attr('src', this.getCardImageUrl('showLeft_', this.cardsLeft[this.selectionLeft]));
			AY.myFadeIn(leftImgField);
			this.changeSelectionLeftCards('+');
		}

		if (this.clickCount === 1 && this.isFirstClickedRightOrLeft.substr(0, 4) === 'left') {
			this.cleanHelp();
			this.cleanMemory();
		}
		this.removeBorderLeft();
	},

	/**
	 * Shows the next cards in the right card browser
	 *
	 * @return {void}     */
	nextCardsRight: function() {
		for (var k = 0; k < this.MAX_CARDS_ON_SIDE; ++k) {
			this.imgNameRight = 'right_' + k;
			var rightImgField = $('#' + this.imgNameRight);

			rightImgField.attr('src', this.getCardImageUrl('showRight_', this.cardsRight[this.selectionRight]));
			AY.myFadeIn(rightImgField);
			this.changeSelectionRightCards('+');
		}

		if (this.clickCount === 1 && this.isFirstClickedRightOrLeft.substr(0, 5) === 'right') {
			this.cleanHelp();
			this.cleanMemory();
		}
		this.removeBorderRight();
	},

	/**
	 * Shows the previous cards in the left card browser
	 *
	 * @return {void}
	 */
	prevCardsLeft: function() {
		for (var i = 0; i < this.MAX_CARDS_ON_SIDE; ++i) {
			this.changeSelectionLeftCards('-');
		}

		this.selectionForCardBrowser = this.selectionLeft;
		this.changeSelectionForCardBrowser('-');

		for (var k = this.MAX_CARDS_ON_SIDE - 1; k >= 0; --k) {
			this.imgNameLeft = 'left_' + k;
			var leftImgField = $('#' + this.imgNameLeft);

			leftImgField.attr('src', this.getCardImageUrl('showLeft_', this.cardsLeft[this.selectionForCardBrowser]));
			AY.myFadeIn(leftImgField);
			this.changeSelectionForCardBrowser('-');
		}

		if (this.clickCount === 1 && this.isFirstClickedRightOrLeft.substr(0, 4) === 'left') {
			this.cleanHelp();
			this.cleanMemory();
		}
		this.removeBorderLeft();
	},

	/**
	 * Shows the previous cards in the right card browser
	 *
	 * @return {void}
	 */
	prevCardsRight: function() {
		for (var i = 0; i < this.MAX_CARDS_ON_SIDE; ++i) {
			this.changeSelectionRightCards('-');
		}

		this.selectionForCardBrowser = this.selectionRight;
		this.changeSelectionForCardBrowser('-');

		for (var k = this.MAX_CARDS_ON_SIDE - 1; k >= 0; --k) {
			this.imgNameRight = 'right_' + k;
			var rightImgField = $('#' + this.imgNameRight);

			rightImgField.attr('src', this.getCardImageUrl('showRight_', this.cardsRight[this.selectionForCardBrowser]));
			AY.myFadeIn(rightImgField);
			this.changeSelectionForCardBrowser('-');
		}

		if (this.clickCount === 1 && this.isFirstClickedRightOrLeft.substr(0, 5) === 'right') {
			this.cleanHelp();
			this.cleanMemory();
		}
		this.removeBorderRight();
	},

	/**
	 * Checks the accuracy of the values from the variables selectionLeft and selectionRight
	 *
	 * @return {void}
	 */
	checkSelectionCards: function() {
		if (this.selectionLeft >= this.cardsLeft.length) {
			this.selectionLeft = 0;
		} else if (this.selectionRight >= this.cardsRight.length) {
			this.selectionRight = 0;
		}
	},

	/**
	 * Increase or decrease the value of the variable selectionLeft
	 *
	 * @param {String} arithmetic
	 * @return {void}
	 */
	changeSelectionLeftCards: function(arithmetic) {
		if (arithmetic === '+') {
			if (this.selectionLeft < this.cardsLeft.length - 1) {
				++this.selectionLeft;
			} else {
				this.selectionLeft = 0;
			}
		} else if (arithmetic === '-') {
			if (this.selectionLeft > 0) {
				--this.selectionLeft;
			} else {
				this.selectionLeft = this.cardsLeft.length - 1;
			}
		}
	},

	/**
	 * Increase or decrease the value of the variable selectionRight
	 *
	 * @param {String} arithmetic
	 * @return {void}
	 */
	changeSelectionRightCards: function(arithmetic) {
		if (arithmetic === '+') {
			if (this.selectionRight < this.cardsRight.length - 1) {
				++this.selectionRight;
			} else {
				this.selectionRight = 0;
			}
		} else if (arithmetic === '-') {
			if (this.selectionRight > 0) {
				--this.selectionRight;
			} else {
				this.selectionRight = this.cardsRight.length - 1;
			}
		}
	},

	/**
	 * Increase or decrease the value of the variable selectionForCardBrowser
	 *
	 * @param {String} arithmetic
	 * @return {void}
	 */
	changeSelectionForCardBrowser: function(arithmetic) {
		if (arithmetic === '+') {
			if (this.selectionForCardBrowser < this.cardsLeft.length - 1) {
				++this.selectionForCardBrowser;
			} else {
				this.selectionForCardBrowser = 0;
			}
		} else if (arithmetic === '-') {
			if (this.selectionForCardBrowser > 0) {
				--this.selectionForCardBrowser;
			} else {
				this.selectionForCardBrowser = this.cardsLeft.length - 1;
			}
		}
	},

	/**
	 * Change the image of the left or right help field
	 *
	 * @param {String} fieldid
	 *
	 * @return {void}
	 */
	deleteTip: function(fieldid) {
		$('#' + fieldid).attr('src', this.placeHolderImage);
	},

	/**
	 * Refresh values of temporary variables
	 * @return {void}
	 */
	cleanMemory: function() {
		this.removeBorder();
		this.clickCount = 0;
		this.clickedCardFieldLeft = '';
		this.clickedCardFieldRight = '';
	},

	/**
	 * Checks if clickCount is 0, than calling cleanHelp()
	 * @return {void}
	 */
	checkCleanHelp: function() {
		if (this.clickCount === 0) {
			this.cleanHelp();
		}
	},

	/**
	 * Removes the border and images from the help boxes
	 *
	 * @return {void}
	 */
	cleanHelp: function() {
		var leftHelp = $('#help_left');
		var rightHelp = $('#help_right');
		var leftHelpError = $('#help_left_error');
		var rightHelpError = $('#help_right_error');
		leftHelp[0].className = 'greyBorder';
		leftHelpError[0].className = 'removeBorder';
		rightHelp[0].className = 'greyBorder';
		rightHelpError[0].className = 'removeBorder';

		leftHelp.attr('src', this.placeHolderImage);
		leftHelpError.attr('src', this.placeHolderImage);
		rightHelp.attr('src', this.placeHolderImage);
		rightHelpError.attr('src', this.placeHolderImage);
	},

	/**
	 * Shows or hides the game help box
	 *
	 * @param {boolean} forceHide
	 * @return {void}
	 */
	showHideHelp: function(forceHide) {
		var tableDataHelp = $('#help');
		var helpStatus = $('#helpStatus');
		if (tableDataHelp[0].className !== 'hide' || forceHide) {
			tableDataHelp[0].className = 'hide';
			helpStatus[0].className = 'hide';
		} else {
			tableDataHelp[0].className = '';
			helpStatus[0].className = '';
		}
	},

	/**
	 * Shows or hides the game information box
	 *
	 * @param {boolean} forceHide
	 * @return {void}
	 */
	showHideGameInfoBox: function(forceHide) {
		var rowInfo = $('#infoText');
		var infoStatus = $('#infoStatus');
		if (rowInfo[0].className !== 'hide' || forceHide) {
			rowInfo[0].className = 'hide';
			infoStatus[0].className = 'hide';
		} else {
			rowInfo[0].className = '';
			infoStatus[0].className = '';
		}
	},

	/**
	 * Change the border of the help fields green
	 *
	 * @return {void}
	 */
	setHelpSuccess: function() {
		$('#help_left')[0].className = 'greenBorder';
		$('#help_left_error')[0].className = 'removeBorder';
		$('#help_right')[0].className = 'greenBorder';
		$('#help_right_error')[0].className = 'removeBorder';
	},

	/**
	 * Change the border of the help fields red
	 *
	 * @return {void}
	 */
	setHelpError: function() {
		$('#help_left')[0].className = 'redBorder';
		$('#help_left_error')[0].className = 'redBorder';
		$('#help_right')[0].className = 'redBorder';
		$('#help_right_error')[0].className = 'redBorder';
	},

	/**
	 * Returns the image number
	 *
	 * @param {String} imgName
	 * @returns {String}
	 */
	getImageValue: function(imgName) {
		var $imgObject = $('#' + imgName);
		if ($imgObject.length <= 0) {
			return '';
		}

		var srcImg = $imgObject.attr('src');
		srcImg = srcImg.substr(srcImg.lastIndexOf('img_'));
		var splitImg = srcImg.split('_');
		return splitImg[1];
	},

	/**
	 * Removes the border of the left and right card browser
	 *
	 * @return {void}
	 */
	removeBorder: function() {
		this.removeBorderLeft();
		this.removeBorderRight();
	},

	/**
	 * Removes the border of the left card browser
	 *
	 * @return {void}
	 */
	removeBorderLeft: function() {
		if (this.clickedCardFieldLeft !== '' && this.clickedCardFieldLeft > 0) {
			$('#left_' + this.clickedCardFieldLeft)[0].className = '';
		} else {
			$('#left_0')[0].className = '';
		}
	},

	/**
	 * Removes the border of the right card browser
	 *
	 * @return {void}
	 */
	removeBorderRight: function() {
		if (this.clickedCardFieldRight !== '' && this.clickedCardFieldRight > 0) {
			$('#right_' + this.clickedCardFieldRight)[0].className = '';
		} else {
			$('#right_0')[0].className = '';
		}
	},

	/**
	 * Shows the card browser
	 *
	 * @return {void}
	 */
	showCardBrowser: function() {
		$('#leftScrollNext')[0].className = '';
		$('#leftScrollPrev')[0].className = '';
		$('#rightScrollNext')[0].className = '';
		$('#rightScrollPrev')[0].className = '';
	},

	/**
	 * Hides the card browser
	 *
	 * @return {void}
	 */
	hideCardBrowser: function() {
		$('#leftScrollNext')[0].className = 'hide';
		$('#leftScrollPrev')[0].className = 'hide';
		$('#rightScrollNext')[0].className = 'hide';
		$('#rightScrollPrev')[0].className = 'hide';
	},

	/**
	 *
	 * @param {string} prefix
	 * @param {number} id
	 * @return {string}
	 */
	getCardImageUrl: function(prefix, id) {
		return this.imageMap[prefix + id];
	},

	/**
	 * Shows or hides card result tables
	 *
	 * @param {int} level
	 * @return {void}
	 */
	showHideCardTables: function(level) {
		level = parseInt(level, 10);
		var allElements = $('#vowels, #conjunctions, #consonants, #numbers');

		var visibleElements = {};
		if (level === 0) {
			visibleElements = allElements;
			this.offsetInImageMap = 0;
		} else if (level === 1) {
			visibleElements = $('#vowels');
			this.offsetInImageMap = 0;
		} else if (level === 2) {
			visibleElements = $('#consonants');
			this.offsetInImageMap = 31;
		} else if (level === 3) {
			visibleElements = $('#numbers');
			this.offsetInImageMap = 64;
		} else if (level === 4) {
			visibleElements = $('#conjunctions');
			this.offsetInImageMap = 74;
		}

		this.imageMap = [];
		if (visibleElements.length) {
			allElements.hide();
			var fadeSpeed = (this.tablesVisible ? 0 : 200);
			this.tablesVisible = true;
			visibleElements.show()
			AY.myFadeIn(visibleElements, fadeSpeed);
			visibleElements.each(function(index, element) {
				element = $(element);
				element.find('img').each(function(index, image) {
					image = $(image);
					this.imageMap[image.attr('id')] = image.attr('src');
				}.bind(this));
			}.bind(this));

		} else {
			this.tablesVisible = false;
			allElements.each(function(index, element) {
				element = $(element);
				AY.myFadeOut(element, 200, function() {
					element.css({
						display: 'none',
						visibility: 'hidden'
					});
				});
			}.bind(this));
		}
	}
};

$(document).ready(function() {
	new AY.DevanagariTrainer();
});
