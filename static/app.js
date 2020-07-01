Vue.component('message-list', {
  props: ['messages'],
  template: `
<div v-if="messages" id="user-messages">
  <ul class="message-list">
    <li v-for="msg in messages" class="error-messages">
      <span class="message-text">{{ msg }}</span>
      <span class="flash-close" v-on:click="removeMessage(msg)">
      X
      </span>
    </li>
  </ul>
</div>
  `,
  data() {
    return {}
  },
  methods: {
    removeMessage(msg) {
      this.$emit('remove-message', msg)
    }
  }
})

Vue.component('error-list', {
  props: ['errors'],
  data () {
    return {}
  },
  template: `
<div class="listing popup errors">
  <p><strong>Some feeds could not be added. Please check that these feeds are valid before trying again</strong></p>
  <div>
    <ul>
      <li v-for="error in errors"> [[ error ]]</li>
    </ul>
  </div>
  <button class="cancel" v-on:click="exit">Exit</button>
</div>
`,
  methods: {
    exit() {
      this.$emit('exit')
    }
  },
  delimiters: ['[[',']]']
})

Vue.component('add-feed', {
  props: ['addingFeed','activeList'],
  data () {
    return {
      url: null
    }
  },
  template: `
<div class="listing popup">
  <label for="url">
  Enter feed or site URL. <br/> 
  e.g. "https://example.com" for a site URL or <br/> 
  "https://example.com/rss" for a feed URL
  </label>
  <input v-model="this.url" id="url" type="url" placeholder="https://example.com/rss"/>
  <div class="add-buttons">
    <button v-on:click="addFeed">Add feed URL</button>
    <button v-on:click="addUrl">Add site URL</button>
  </div>
  <button class="cancel listing" v-on:click="cancelAddFeed">Cancel</button>
</div>
`,
  methods: {
    cancelAddFeed() {
      this.$emit('cancel-addfeed')
    },
    addFeed() {
      payload = {
        "feed" : url,
        "list_id" : this.activeList.list_id
      }
      url = null
      this.$emit('add-feed', payload)
    },
    addUrl() {
      payload = {
        "url" : url,
        "list_id" : this.activeList.list_id
      }
      url = null
      this.$emit('add-feed', payload)
    }
  },
  delimiters: ['[[',']]']
})

Vue.component('add-list', {
  props: ['addingList'],
  data () {
    return {
      show: true
    }
  },
  template: `
<div class="listing popup" v-show="show">
  <form v-on:submit.prevent="addList">
      <label for="listname">Enter a name for your list</label>
      <input id="listname" name="listname" type="text"/>
      <button class="listing">Add List</button>
    </form>
    <form v-on:submit.prevent="uploadOpml">
      <label for="opml">...Or upload an OPML file</label>
      <input type="file" id="opml" name="opml">
      <button class="listing">Upload OPML</button>
    </form>
    <button class="listing cancel" v-on:click="cancelAddList">Cancel</button>
</div>
  `,
  methods: {
    addList(e) {
      let name = e.target.listname.value
      this.$emit('add-list', name)
    },
    cancelAddList() {
      this.$emit('cancel-addlist')
    },
    uploadOpml(event) {
      this.$emit('loading', true)
      this.show = false
      const formData = new FormData()
      const file = event.target.opml.files[0]
      if (file) {
        formData.append('file', file)
        return axios.post('/upload-opml', formData,{
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        .then( res => {
          this.$emit('adding', true)
          this.$emit('set-total', res.data.feeds.length)
          if (res.data.feeds) {
            var total = 0
            var errors = []
            for (let f of res.data.feeds) {
                axios.post('/add-from-opml', {
                  "feed" : f.url,
                  "category" : f.category
                })
                .then( resp => {
                  if (resp.data.status !== "ok") {
                    errors.push(f.url)
                  }
                  this.$emit('increment')
                  total += 1
                  if (total >= res.data.feeds.length) {
                    this.show = true
                    this.$emit('opml-completed')
                    this.$emit('show-errors', errors)
                  }
                })
                .catch(err => {
                  this.$emit('add-message', err)
                  this.$emit('loading', false)
                })
              }
          } else {
            this.$emit('add-message', res.data.error)
            this.$emit('loading', false)
          }
        })
        .catch(err => {
          this.$emit('add-message', err)
          this.$emit('loading', false)
        })
      } else {
        this.$emit('add-message', 'You need to attach your OPML file before you can upload it!')
        this.$emit('cancel-addlist')
        this.$emit('loading', false)
      }
    }
  },
})

Vue.component('manage-list', {
  props: ['activeList'],
  template: `
<div class="listing popup">
  <form v-on:submit.prevent="renameList">
    <label for="listname">Enter a name for your list</label>
    <input id="listname" name="list_name" type="text"/>
    <button class="listing">Rename List</button>
  </form>
  <button class="listing" v-on:click="deleteList">Delete list</button>
  <button class="listing cancel" v-on:click="cancelManage">Cancel</button>
</div>
  `,
  methods: {
    cancelManage() {
      this.$emit('cancel-manage')
    },
    deleteList() {
      this.$emit('loading', true)
      this.$emit('delete-list', this.activeList.list_id)
    },
    renameList(e) {
      this.$emit('loading', true)
      payload = {
        "list_id" : this.activeList.list_id,
        "list_name" : e.target.list_name.value
      }
      this.$emit('rename-list', payload)
    }
  },
  delimiters: ['[[',']]']
})

Vue.component('manage-feed', {
  props: ['feed', 'list'],
  template: `
<div class="listing popup">
  <button class="listing" v-on:click="deleteFeed">Delete Feed</button>
  <button class="listing cancel" v-on:click="cancelManage">Cancel</button>
</div>
  `,
  methods: {
    cancelManage() {
      this.$emit('cancel-manage')
    },
    deleteFeed() {
      this.$emit('loading', true)
      this.$emit('delete-feed', {"feed" : this.feed, "list" : this.list.list_id})
    }
  },
  delimiters: ['[[',']]']
})

Vue.component('manage-account', {
  data () {
    return {
      check : false
    }
  },
  template: `
<div class="listing popup">
  <template v-if="check">
    <div>Are you sure you want to delete your whole Empocketer account? You will lose all lists and feeds.</div>
    <button class="listing cancel" v-on:click="cancelManage">NO! Take me back</button>
    <a href="/delete-user"><button class="listing">Yes I hate this stupid app</button></a>
  </template>
  <template v-else>
  <a href="/logout"><button class="listing">Log Out</button></a>
  <button class="listing" v-on:click="areYouSure">Delete account</button>
  <button class="listing cancel" v-on:click="cancelManage">Cancel</button>
  </template>
</div>
  `,
  methods: {
    cancelManage() {
      this.$emit('cancel-manage')
    },
    areYouSure() {
      this.check = true
    }
  },
  delimiters: ['[[',']]']
})

var vm = new Vue({
  el: '#app',
  data () {
    return {
      activeList: {},
      addingFeed: false,
      addingFeeds: false,
      addingList: false,
      errors: [],
      feedsAdded: 0,
      lists: [],
      loading: false,
      managingFeed: false,
      managingList: false,
      managingUser: false,
      messages: [],
      showingErrors: false,
      totalFeedsToAdd: 0,
      user: null
    }
  },
  mounted () {
    axios.get('/user-details')
    .then( res => {
      this.user = res.data.username
      this.lists = res.data.lists
      if (this.lists.length > 0) {
        Vue.set(this.lists[0], 'isActive', true)
        this.activeList = this.lists[0]
      }
    })
    .catch(err => {
      this.messages.push(err)
    })
  },
  methods: {
    addFeed (data) {
      if ((typeof data.feed == 'string') || (typeof data.url == 'string')) {
        this.loading = true
        this.addingFeed = false
        axios.post('/add-feed', data)
        .then( res => {
          if (res.data.status === "ok") {
            i = this.lists.indexOf(this.activeList)
            this.lists[i].feeds.push(res.data.feed)
          } else {
            let err = res.data.error
            if (err.slice(0,6) == "UNIQUE") {
              err = "That feed is already in this list!"
            }
            this.messages.push(err)
          }
          this.loading = false
        })
        .catch(err => {
          this.messages.push(err)
        })
      } else {
        this.messages.push('You must enter a URL to add a feed')
        this.addingFeed = false
      }
    },
    addList (listname) {
      this.loading = true
      this.addingList = false
      if (listname) {
        axios.post('/add-list', { "list_name" : listname})
        .then( res => {
          if (res.data.status === "ok") {
            let i = this.lists.length
            Vue.set(this.lists, i, {
              "name" : listname,
              "list_id" : res.data.list_id,
              "feeds" : []
            })
            if (i > 0) {
              a = this.lists.indexOf(this.activeList)
              Vue.set(this.lists[a], 'isActive', false)
            }
            Vue.set(this.lists[i], 'isActive', true)
            this.activeList = this.lists[i]
            this.loading = false
          } else {
            this.messages.push(res.data.error)
          }
        })
        .catch(err => {
          this.messages.push(err)
        })
      } else {
        this.messages.push('You must enter a name for your list')
        this.addingList = false
        this.loading = false
      }
    },
    addMessage(msg) {
      this.messages.push(msg)
    },
    cancelAddFeed () {
      this.addingFeed = false
    },
    cancelAddList () {
      this.addingList = false
    },
    cancelManage () {
      this.managingUser = false
      this.managingList = false
      this.managingFeed = false
    },
    deleteFeed (args) {
      this.managingFeed = false
      axios.post('/delete-feed', {
        "feed_id" : args.feed.feed_id
      })
      .then( res => {
        if (!res.data.error) {
          let l = x => x.list_id == args.list
          let i = this.lists.findIndex(l)
          let index = this.lists[i].feeds.indexOf(args.feed)
          Vue.delete(this.lists[i].feeds, index)
        } else {
          this.messages.push(res.data.error)
        }
        this.loading = false
      })
      .catch(err => {
        this.messages.push(err)
      })
    },
    deleteList (list_id) {
      this.managingList = false
      axios.post('/delete-list', {"list_id" : list_id})
      .then( res => {
        if (!res.data.error) {
          let l = x => x.list_id == list_id
          let i = this.lists.findIndex(l)
          this.activeList = {}
          Vue.delete(this.lists, i)
          if (this.lists.length > 0) {
            Vue.set(this.lists[0], 'isActive', true)
            this.activeList = this.lists[0]
          } else {
            this.activeList = {}
          }
        } else {
          this.messages.push(res.data.error)
        }
        this.loading = false
      })
      .catch(err => {
        this.messages.push(err)
      })
    },
    exitErrors () {
      this.showingErrors = false
      this.errors = []
    },
    incrementFeeds() {
      this.feedsAdded += 1
    },
    manageFeed (feed) {
      this.managingFeed = feed
    },
    removeMessage(msg) {
      // fired when click on X to get rid of it
      Vue.delete(this.messages, this.messages.indexOf(msg))
    },
    renameList (data) {
      this.managingList = false
      if (data.list_name) {
        axios.post('/rename-list', data)
        .then( res => {
          if (!res.data.error) {
            let l = (x) => x.list_id == data.list_id
            let i = this.lists.findIndex(l)
            Vue.set(this.lists[i], 'name', data.list_name)
          } else {
            this.messages.push(res.data.error)
          }
          this.loading = false
        })
        .catch(err => {
          this.messages.push(err)
        })
      } else {
        this.messages.push('You must enter a name to rename your list')
        this.loading = false
      }
    },
    resetAll () {
      axios.get('/user-details')
      .then( res => {
        this.user = res.data.username
        this.lists = res.data.lists
        this.addingList = false
        this.addingFeeds = false
        this.totalFeedsToAdd = 0
        this.feedsAdded = 0
        Vue.set(this.lists[0], 'isActive', true)
        this.activeList = this.lists[0]
        this.loading = false
      })
      .catch(err => {
        this.messages.push(err)
      })
    },
    setActive (index) {
      // if this is the active list, activate the list popup
      if (this.activeList == this.lists[index] ) {
        this.managingList = true
      } else {
        // make this list the active list
        for (let list of this.lists) {
          Vue.set(list, 'isActive', false)
        }
        Vue.set(this.lists[index], 'isActive', true)
        this.activeList = this.lists[index] 
      }
    },
    setAdding() {
      this.addingFeeds = true
    },
    setLoading(bool) {
      if (bool) {
        this.loading = true
      } else {
        this.loading = false
        this.addingFeeds = false
        this.totalFeedsToAdd = 0
        this.feedsAdded = 0
      }
    },
    setTotal(val) {
      this.totalFeedsToAdd = val
    },
    showErrors (errors) {
      this.errors = errors
      this.showingErrors = true
    }
  },
  delimiters: ['[[',']]']
})