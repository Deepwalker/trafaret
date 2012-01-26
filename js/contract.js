(function() {

   var TrafaretValidationError = function(message, original_message, name) {
     this.message = message;
     this.original_message = original_message;
     this.name = name;
   };

   var Trafaret = function() {

   };

   Trafaret.prototype.failure = function(message) {
     throw new TrafaretValidationError(message, message, null);
   };

   Trafaret.prototype._select = function(value, default_val) {
     if (typeof value == "undefined") {
       return default_val;
     } else {
       return value;
     }
   };

   Trafaret.prototype.check = function() {
     throw "not implemented";
   };

   var AnyC = function() {

   };

   AnyC.prototype = new Trafaret();

   AnyC.prototype.check = function() {

   };

   var OrC = function() {
     this.contracts = [];
     for (var i=0, length = arguments.length; i < length; i++) {
       this.contracts.push(arguments[i]);
     }
   };

   OrC.prototype = new Trafaret();

   OrC.prototype.check = function(value) {
     for (var i=0, length=this.contracts.length; i < length; i++) {
       try {
	 this.contracts[i].check(value);
	 return;
       } catch (e) {
	 if (! (e instanceof TrafaretValidationError)) {
	   throw e;
	 }
       }
     }
     this.failure("no one contract matches");
   };

   var NullC = function() {

   };

   NullC.prototype = new Trafaret();

   NullC.prototype.check = function(value) {
     if (value !== null) {
       this.failure("value should be null");
     }
   };

   var BoolC = function() {

   };

   BoolC.prototype = new Trafaret();

   BoolC.prototype.check = function(value) {
     if (typeof value != "boolean") {
       this.failure("value should be boolean");
     }
   };

   var IntC = function(min, max) {
     this.min = this._select(min, NaN);
     this.max = this._select(max, NaN);
   };

   IntC.prototype = new Trafaret();

   IntC.prototype.check_min = function(value) {
     if (! isNaN(this.min) && value < this.min) {
       this.failure("value is less than " + this.min);
     }
   };

   IntC.prototype.check_max = function(value) {
     if (! isNaN(this.max) && value > this.max) {
       this.failure("value is greater than " + this.max);
     }
   };

   IntC.prototype.check = function(value) {
     if (typeof value != "number" || /.*\..*/.test(value.toString())) {
       this.failure("value is not int");
     }
     this.check_min(value);
     this.check_max(value);
   };

   var FloatC = function(min, max) {
     this.min = this._select(min, NaN);
     this.max = this._select(max, NaN);
   };

   FloatC.prototype = new IntC(NaN, NaN);

   FloatC.prototype.check = function(value) {
     if (typeof value != "number") {
       this.failure("value is not float");
     }
     this.check_min(value);
     this.check_max(value);
   };

   var StringC = function(allow_blank) {
     this.allow_blank = this._select(allow_blank, false);
   };

   StringC.prototype = new Trafaret();

   StringC.prototype.check = function(value) {
     if (typeof value != "string") {
       this.failure("value is not string");
     }
     if (! this.allow_blank && ! value.length) {
       this.failure("blank value is not allowed");
     }
   };

   var ListC = function(contract, min_length, max_length) {
     this.contract = contract;
     this.min_length = this._select(min_length, NaN);
     this.max_length = this._select(max_length, NaN);
   };

   ListC.prototype = new Trafaret();

   ListC.prototype.check = function(value) {
     if (! (value instanceof Array)) {
       this.failure("value is not list");
     }
     if (! isNaN(this.min_length) && value.length < this.min_length) {
       this.failure("list length is less than " + this.min_length);
     }
     if (! isNaN(this.max_length) && value.length > this.max_length) {
       this.failure("list length is greater than " + this.max_length);
     }
     var name, message;
     for (var i=0, length=value.length; i < length; i++) {
       try{
	 this.contract.check(value[i]);
       } catch (e) {
	 if (e instanceof TrafaretValidationError) {
	   name = e.name;
	   if (e.name) {
	     name = i.toString() + "." + e.name;
	   } else {
	     name = i.toString();
	   }
	   message = name + ": " + e.original_message;
	   throw new TrafaretValidationError(message, e.original_message, name);
	 }
	 throw e;
       }

     }
   };

   window["TrafaretValidationError"] = TrafaretValidationError,
   window["AnyC"] = AnyC,
   window["NullC"] = NullC,
   window["IntC"] = IntC,
   window["FloatC"] = FloatC,
   window["StringC"] = StringC,
   window["BoolC"] = BoolC,
   window["OrC"] = OrC,
   window["ListC"] = ListC;

 })();