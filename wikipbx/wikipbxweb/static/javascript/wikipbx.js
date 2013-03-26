
function load() {

}


function getNumJoinPplFields() {
  var form_fields = $('form_fields');
  var input_elts = form_fields.getElementsByTagName("div");
  var input_text_elts = new Array();
  for (i=0; i<input_elts.length; i++) {
     if (input_elts[i].id.indexOf("participant") != -1) {
         input_text_elts[i] = input_elts[i];
     }
  }
  return input_text_elts.length;
}

function joinMorePeople() {
    numPeopleJoined = getNumJoinPplFields(); 
    id2use = numPeopleJoined + 1

    div = DIV({id: "participant_"+id2use, style: "padding-top: 1em", numeric_id: id2use});
    appendChildNodes(div, "# to dial: ");    
    appendChildNodes(div, INPUT({type:"text", name:"number_"+id2use, id:"number_"+id2use}));  
    select = SELECT({name:"concurrent_number_"+id2use, id:"concurrent_number_"+id2use});
    appendChildNodes(select, OPTION({value:"1"},"1"));
    appendChildNodes(select, OPTION({value:"2"},"2"));
    appendChildNodes(select, OPTION({value:"3"},"3"));
    appendChildNodes(select, OPTION({value:"4"},"4"));
    appendChildNodes(select, OPTION({value:"5"},"5"));
    appendChildNodes(select, OPTION({value:"10"},"10"));
    appendChildNodes(select, OPTION({value:"25"},"25"));
    appendChildNodes(select, OPTION({value:"100"},"100"));
    appendChildNodes(select, OPTION({value:"500"},"500"));
    appendChildNodes(div, SPAN({style: "padding-left: 1em"}, " # concurrent: "));    
	appendChildNodes(div, select);    	
    appendChildNodes($('form_fields'),div);    
    return id2use

}

function getEmptyRow() {
    // if there is an empty 'row', return it.
    // the row referred to is a pair of name/number phone inputs
    // empty means there is no number input (ignore name)
    var form_fields = $('form_fields');
    var input_elts = form_fields.getElementsByTagName("div");
    for (i=0; i<input_elts.length; i++) {
       if (input_elts[i].id.indexOf("participant") != -1) {
           numeric_id = input_elts[i].getAttribute('numeric_id')
            number_input = $("number_"+numeric_id);
           if (!number_input.value) {
               // ah, an empty row .. return it
               return numeric_id 
           }
       }
    }
    return null;

}

function getOrCreateEmptyRow() {
    // get 1st empty row or null
    emptyRowId = getEmptyRow()
    if (!emptyRowId) {
        // otherwise call joinMorePeople() to make new row
        // and return that row
        emptyRowId = joinMorePeople()
    }
    return emptyRowId
}
