awsRegions = [
    {value: 'us-east-1', text: 'US East (N. Virginia)'},
    {value: 'us-east-2', text: 'US East (Ohio)'},
    {value: 'us-west-1', text: 'US West (N. California)'},
    {value: 'us-west-2', text: 'US West (Oregon)'},
    {value: 'ap-east-1', text: 'Asia Pacific (Hong Kong)'},
    {value: 'ap-south-1', text: 'Asia Pacific (Mumbai)'},
    {value: 'ap-northeast-2', text: 'Asia Pacific (Seoul)'},
    {value: 'ap-southeast-1', text: 'Asia Pacific (Singapore)'},
    {value: 'ap-southeast-2', text: 'Asia Pacific (Sydney)'},
    {value: 'ap-northeast-1', text: 'Asia Pacific (Tokyo)'},
    {value: 'ca-central-1', text: 'Canada (Central)'},
    {value: 'eu-central-1', text: 'EU (Frankfurt)'},
    {value: 'eu-west-1', text: 'EU (Ireland)'},
    {value: 'eu-west-2', text: 'EU (London)'},
    {value: 'eu-west-3', text: 'EU (Paris)'},
    {value: 'eu-north-1', text: 'EU (Stockholm)'},
    {value: 'sa-east-1', text: 'South America (São Paulo)'}
]

azureRegions = [
    {value: 'Central US', text: 'Central US'},
    {value: 'East US', text: 'East US'},
    {value: 'East US 2', text: 'East US 2'},
    {value: 'North Central US', text: 'North Central US'},
    {value: 'South Central US', text: 'South Central US'},
    {value: 'West Central US', text: 'West Central US'},
    {value: 'West US', text: 'West US'},
    {value: 'West US 2', text: 'West US 2'},
    {value: 'North Europe', text: 'North Europe'},
    {value: 'West Europe', text: 'West Europe'},
    {value: 'East Asia', text: 'East Asia'},
    {value: 'Southeast Asia', text: 'Southeast Asia'},
    {value: 'Japan East', text: 'Japan East'},
    {value: 'Japan West', text: 'Japan West'},
    {value: 'Brazil South', text: 'Brazil South'},
    {value: 'Australia Central', text: 'Australia Central'},
    {value: 'Australia East', text: 'Australia East'},
    {value: 'Australia Central 2', text: 'Australia Central 2'},
    {value: 'Australia Southeast', text: 'Australia Southeast'},
    {value: 'Central India', text: 'Central India'},
    {value: 'South India', text: 'South India'},
    {value: 'West India', text: 'West India'},
    {value: 'Canada Central', text: 'Canada Central'},
    {value: 'Canada East', text: 'Canada East'},
    {value: 'UK South', text: 'UK South'},
    {value: 'UK West', text: 'UK West'},
    {value: 'France Central', text: 'France Central'},
    {value: 'France South', text: 'France South'},
    {value: 'Korea Central', text: 'Korea Central'},
    {value: 'Korea South', text: 'Korea South'},
]

clouds = [
    {value: 'aws', text: 'AWS'},
    {value: 'azure', text: 'Azure'}
    // {value: 'google', text: 'Google'}
]

var myChart;

var app = new Vue({
    el: '#app',
    data: function () {
	return {
	    selectedCloud: 'aws',
	    cloudOptions: clouds,
	    selectedRegion:'us-east-1',
	    regionOptions: awsRegions,
            items: [
		{
		    workloadName: '',
		    quantity: 1,
		    utilization: 100,
		    cpu: 1,
		    memory: 1,
		    blockStorage: 0
		}
	    ],
	    cost: null,
	    costDetails: null,
	    costComparisonChart: null,
	}
    },

    updated: function () {
	feather.replace()
	this.createChart();
    },

    methods: {
	toDollar: function(val) {
	    return (val).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
	},
    	onSubmit: function(event) {
	    console.log("submit")
	    event.preventDefault()
	    // "this" variable changes inside handling the response so
	    // I'll capture "this" outside handling the response
	    v = this
	    axios.post('/cost', {
		items: this.items,
		cloud: this.selectedCloud,
		region: this.selectedRegion
	    })
		.then(function (response) {
		    console.log(response.data);
		    v.cost = response.data;
		    v.costDetails = response.data.details;
		    v.costComparisonChart = response.data.costComparisonChart;
		})
		.catch(function (error) {
		    console.log(error);
		});
    	},
    	addRow: function (event) {
	    console.log("add row");
	    event.preventDefault();
    	    this.items.push({
		workloadName: '',
		quantity: 1,
		utilization: 100,
		cpu: 1,
		memory: 1,
		blockStorage: 0
	    });
	},
	onDeleteRow: function(index) {
	    console.log("delete row");
	    this.items.splice(index, 1);
	},
	onChangeCloud: function(selection) {
	    console.log("change cloud: " + selection);
	    if (selection == 'aws') {
		this.regionOptions = awsRegions;
	    } else if (selection == 'azure') {
		this.regionOptions = azureRegions;
	    } else {
		this.regionOptions = awsRegions
	    }
	    this.cost = null
	    this.costDetails = null
	    this.selectedRegion = this.regionOptions[0].value
	},
	createChart: function() {
	    if (this.costComparisonChart != null) {
		console.log("Creating chart")
	    	ctx = document.getElementById('myChart');
		if (myChart) {
		    myChart.destroy();
		}
	    	myChart = new Chart(ctx, this.costComparisonChart);
	    } else {
		console.log("Not creating chart")
	    }
	}
    },
    computed: {
	showCost: function() {
	    return this.cost != null;
	},
	showComparison: function() {
	    return this.costComparisonChart != null;
	}
    },
    delimiters: ["[[","]]"]
})


// Vue.component('vm-entry', {
//   data: function () {
//     return {
//       cpu: 1
//     }
//   },
//   template: '<label for="vm_group_1">VM Group Name</label>'
// })

// Vue.component('vm-group', {
//   data: function () {
//     return {
// 	groupName: '',
// 	quantity: 1,
// 	cpu: 1,
// 	memory: 1
//     }
//   },
//   template: '

// <button v-on:click="count++">You clicked me {{ count }} times.</button>'
// })

// var app = new Vue({
//     el: '#app',
//     data: function () {
// 	return {
//             items: [
// 		{
// 		    id: 'item1',
// 		    value: 'one'
// 		},
// 		{
// 		    id: 'item2',
// 		    value: 'two'
// 		}
// 	    ]
// 	}
//     },
//     methods: {
// 	addRow: function (event) {
// 	    numItems = this.items.length + 1
// 	    name = 'item' + numItems
// 	    this.items.push({id: name, value: name})
// 	}
//     },
//     delimiters: ["[[","]]"]
// })
