var request = require('request');
var cheerio = require('cheerio');
var http = require('http');
var fs = require('fs');
var unoconv = require('unoconv');

var addressbook={
  type: "FeatureCollection",
  features: []
};

var areas = JSON.parse(fs.readFileSync('section2.json', 'utf-8')).area;
var areaIDs = JSON.parse(fs.readFileSync('section2.json', 'utf-8')).areaID;
var sectionIDs = JSON.parse(fs.readFileSync('section2.json', 'utf-8')).section; 

function findSections(parentstring){
	keys= Object.keys(areas);
	var findCity=null;
	var findArea=null;
    var findcityIdx=-1;
	var findareaIdx=-1;
	for(var i=0;i<keys.length;i++){
		var keyCity=keys[i].substr(0,2);
		var keyArea=keys[i].substr(3);
		var cityIdx=parentstring.indexOf(keyCity);
		var areaIdx=parentstring.indexOf(keyArea);
		if(cityIdx!=-1)
		{
			var substring=parentstring.substr(cityIdx);
			//console.log('find city',substring);
			findCity=keyCity;
		    findcityIdx=cityIdx;
		}
		if(areaIdx!=-1)
		{
			var substring=parentstring.substr(areaIdx);
			//console.log('find area',substring);
			findArea=keyArea;
			findareaIdx=areaIdx;
		}
	}
	return [findcityIdx, findCity, findareaIdx, findArea];
}

function findCitybyArea(parentstring){
	keys= Object.keys(areas);
	var cityIdx=-1;
	var areaIdx=-1;
	for(var i=0;i<keys.length;i++){
		var keyCity=keys[i].substr(0,3);
		var keyArea=keys[i].substr(3);
		cityIdx=parentstring.indexOf(keyCity);
		areaIdx=parentstring.indexOf(keyArea);
		if(areaIdx!=-1)
		{
		  console.log('find area', keys[i], keyCity, keyArea);
		  break;
		}
	}
	return [cityIdx, areaIdx, keyCity];
}

function findAreabySection(parentstring, city, area){
	keys= Object.keys(sectionIDs);
	var areaidx=-1;
	var idx=-1;
	var find=0;
	var i, j;
	var findarea=''
	for(i=0;i<keys.length;i++){
		var sections=Object.keys( sectionIDs[keys[i]]);
		//console.log(keys[i], areaIDs[keys[i]], sectionIDs[keys[i]]);
		for(j=0;j<sections.length;j++){
			idx=parentstring.indexOf(sections[j]);
			if( (city!=null && areaIDs[keys[i]].indexOf(city)!=-1) || (city==null & area==null) || (area!=null && areaIDs[keys[i]].indexOf(area)!=-1)){
			  //console.log(city, area, areaIDs[keys[i]], sections[j]);
			  if(idx!=-1){
				console.log('find seciton',sections[j], areaIDs[keys[i]]);
			    find=1;
				findarea=areaIDs[keys[i]];
				break;
			  }
			}  
		}
		if(find){
		   break;	
		}
		  
	}
	return [idx, findarea];
}

function ParseMapNum_address2(i, foldername, files){
    var filename=foldername+'/'+files[i];
	if (filename.indexOf('.html')==-1)
	{
		if((i+1) < files.length){
			 ParseMapNum_address2(i+1, foldername, files);
		}
		return;
	}
	var content = fs.readFileSync(filename,'utf-8');
	var $ = cheerio.load(content);
	content = content.replace(/<style([\s\S]*?)<\/style>/gi, '');
    content = content.replace(/<script([\s\S]*?)<\/script>/gi, '');
	content = content.replace(/<\/div>/ig, '\n');
	content = content.replace(/<\/li>/ig, '\n');
	content = content.replace(/<li>/ig, '  *  ');
	content = content.replace(/<\/ul>/ig, '\n');
	content = content.replace(/<\/p>/ig, '\n');
	content = content.replace(/<br\s*[\/]?>/gi, "\n");
	content = content.replace(/<[^>]+>/ig, '');
	//console.log(content);
	var googlemapLink='http://maps.google.com/maps/api/geocode/json?sensor=false&language=zh-tw®ion=tw&address=';
	id=parseInt(files[i].substr(files[i].indexOf('(')+1, files[i].indexOf(')')-1));
	title=files[i].substr(0,files[i].indexOf('.html'));
	console.log(title);
	var regex = /設施地址/; 
	var startIdx, endIdx, lineIdx;
	var myArray = regex.exec(content);
	startIdx=myArray['index'];
	//console.log(startIdx);
	var addresstext=content.substr(startIdx+4,content.length);
	//console.log('address raw 設施地址 ',addresstext); 
	regex = /主管機關/; 
	myArray = regex.exec(addresstext);
	endIdx=myArray['index'];
	//console.log(endIdx);
	var address=addresstext.substr(0,endIdx);
	//console.log('address raw 主管機關 ',address); 
	address=address.replace(/\n/g,'');
	address=address.replace(new RegExp('台', 'g'),"臺");
	startIdx=findSections(address);
	address=address.substr(startIdx,address.length);
	//console.log(address);
	googlemapLink=googlemapLink+address;
	//console.log(googlemapLink);
    request(googlemapLink, function (error, response, data) {
		result=JSON.parse(data);
		if(result['status']=='OK'){
			var point=result['results'][0]['geometry']['location'];
			var coor = new Array();
			coor.push(point['lng']);
			coor.push(point['lat']);
			addressbook.features.push({
				  type: 'Feature',
				  properties: {
				  'Title': title,
				  'MapAddress': address,
				  'ID':id
				  },
				  geometry: {
					type: 'Point',
					coordinates: coor
				  }
			});
			fs.writeFileSync('NoUseAddressbook.json', JSON.stringify(addressbook), "UTF-8", {'flags': 'w+'});
		}
		if((i+1) < (files.length-1)){
			 ParseMapNum_address2(i+1, foldername, files);
		}
	});	
}

//console.log(process.argv);
var foldername=process.argv[2];
var files = fs.readdirSync(foldername);
ParseMapNum_address2(0, foldername, files);

