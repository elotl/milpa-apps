var app = new Vue({
    el: '#app',
    data: function () {
	return {
            items: [
		{
		    workloadName: '',
		    quantity: 1,
		    cpu: 1,
		    memory: 1,
		    blockStorage: 0
		}
	    ],
	    cost: null,
	    costDetails: null,
	}
    },
    updated: function () {
	feather.replace()
    },
    methods: {
    	onSubmit: function(event) {
	    event.preventDefault()
	    // "this" variable changes inside handling the response so
	    // I'll capture "this" outside handling the response
	    v = this
	    axios.post('/cost', {
		items: this.items
	    })
		.then(function (response) {
		    console.log(response.data);
		    v.cost = response.data;
		    v.costDetails = response.data.details;
		})
		.catch(function (error) {
		    console.log(error);
		});
    	},
    	addRow: function (event) {
	    // event.preventDefault()
    	    this.items.push({
		    workloadName: '',
		    quantity: 1,
		    cpu: 1,
		    memory: 1,
		    blockStorage: 0
	    })
	},
	onDeleteRow: function(index) {
	    this.items.splice(index, 1)
	}
    },
    computed: {
	showCost: function() {
	    return this.cost != null
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
