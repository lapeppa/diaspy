import requests
import re
import json
import diaspy.models


class Client:
    """This is the client class to connect to diaspora.

    """

    def __init__(self, pod, username, password):
        """
        :param pod: The complete url of the diaspora pod to use.
        :type pod: str
        :param username: The username used to log in.
        :type username: str
        :param password: The password used to log in.
        :type password: str

        """
        self._token_regex = re.compile(r'content="(.*?)"\s+name="csrf-token')
        self.pod = pod
        self.session = requests.Session()
        self._login(username, password)

    def get_token(self):
        """This function gets a token needed for authentication in most cases

        :returns: string -- token used to authenticate

        """

        r = self.session.get(self.pod + '/stream')
        token = self._token_regex.search(r.text).group(1)
        return token

    def _login(self, username, password):
        """This function is used to connect to the pod and log in.
        .. note::
           This function shouldn't be called manually.
        """
        self._username = username
        self._password = password
        #r = self.session.get(self.pod + '/users/sign_in')
        #token = self._token_regex.search(r.text).group(1)

        data = {'user[username]': self._username,
                'user[password]': self._password,
                'authenticity_token': self.get_token()}

        r = self.session.post(self.pod +
                              '/users/sign_in',
                              data=data,
                              headers={'accept': 'application/json'})

        if r.status_code != 201:
            raise Exception(str(r.status_code) + ': Login failed.')

    def post(self, text, aspect_id='public', photos=None):
        """This function sends a post to an aspect

        :param text: Text to post.
        :type text: str
        :param aspect_id: Aspect id to send post to.
        :type aspect_id: str

        :returns: diaspy.models.Post -- the Post which has been created

        """
        data = {'aspect_ids': aspect_id,
                'status_message': {'text': text}}

        if photos:
            data['photos'] = photos
        r = self.session.post(self.pod +
                              "/status_messages",
                              data=json.dumps(data),
                              headers={'content-type': 'application/json',
                                       'accept': 'application/json',
                                       'x-csrf-token': self.get_token()})
        if r.status_code != 201:
            raise Exception(str(r.status_code) + ': Post could not be posted.')

        return diaspy.models.Post(str(r.json()['id']), self)

    def get_user_info(self):
        """This function returns the current user's attributes.

        :returns: dict -- json formatted user info.

        """
        r = self.session.get(self.pod + '/bookmarklet')
        regex = re.compile(r'window.current_user_attributes = ({.*})')
        userdata = json.loads(regex.search(r.text).group(1))
        return userdata

    def post_picture(self, filename):
        aspects = self.get_user_info()['aspects']
        params = {}
        params['photo[pending]'] = 'true'
        params['set_profile_image'] = ''
        params['qqfile'] = filename
        for i, aspect in enumerate(aspects):
            params['photo[aspect_ids][%d]' % (i)] = aspect['id']

        data = open(filename, 'rb')

        headers = {'content-type': 'application/octet-stream',
                   'x-csrf-token': self.get_token(),
                   'x-file-name': filename}

        r = self.session.post(self.pod + '/photos',
                              params=params, data=data, headers=headers)

        return r

    def get_stream(self):
        """This functions returns a list of posts found in the stream.

        :returns: list -- list of Post objects.

        """

        data = {'authenticity_token': self.get_token()}
        r = self.session.get(self.pod + "/stream.json")

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

        stream = r.json()

        posts = []

        for post in stream:
            posts.append(diaspy.models.Post(str(post['id']), self))

        return posts

    def get_notifications(self):
        """This functions returns a list of notifications.

        :returns: list -- list of json formatted notifications

        """

        data = {'authenticity_token': self.get_token()}
        r = self.session.get(self.pod + "/notifications.json")

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

        notifications = r.json()
        return notifications

    def get_mentions(self):
        """This functions returns a list of
        posts the current user is being mentioned in.

        :returns: list -- list of Post objects

        """

        data = {'authenticity_token': self.get_token()}
        r = self.session.get(self.pod + "/mentions.json")

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

        mentions = r.json()

        posts = []

        for post in mentions:
            posts.append(diaspy.models.Post(str(post['id']), self))

        return posts

    def get_tag(self, tag):
        """This functions returns a list of posts containing the tag.
        :param tag: Name of the tag
        :type tag: str

        :returns: list -- list of Post objects

        """

        data = {'authenticity_token': self.get_token()}
        r = self.session.get(self.pod + '/tags/' + tag + '.json')

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

        tagged_posts = r.json()

        posts = []

        for post in tagged_posts:
            posts.append(diaspy.models.Post(str(post['id']), self))

        return posts

    def add_user_to_aspect(self, user_id, aspect_id):
        """ this function adds a user to an aspect.

        :param user_id: User ID
        :type user_id: str
        :param aspect_id: Aspect ID
        :type aspect_id: str

        """

        data = {'authenticity_token': self.get_token(),
                'aspect_id': aspect_id,
                'person_id': user_id}

        r = self.session.post(self.pod + '/aspect_memberships.json',
                              data=data)

        if r.status_code != 201:
            raise Exception('wrong status code: ' + str(r.status_code))
        return r.json()

    def remove_user_from_aspect(self, user_id, aspect_id):
        """ this function removes a user from an aspect.

        :param user_id: User ID
        :type user_id: str
        :param aspect_id: Aspect ID
        :type aspect_id: str

        """

        data = {'authenticity_token': self.get_token(),
                'aspect_id': aspect_id,
                'person_id': user_id}

        r = self.session.delete(self.pod + '/aspect_memberships/42.json',
                                data=data)

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

        return r.json()

    def add_aspect(self, aspect_name, visible=0):
        """ This function adds a new aspect.
        """

        data = {'authenticity_token': self.get_token(),
                'aspect[name]': aspect_name,
                'aspect[contacts_visible]': visible}

        r = self.session.post(self.pod + '/aspects',
                              data=data)

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

    def remove_aspect(self, aspect_id):
        """ This function adds a new aspect.
        """

        data = {'authenticity_token': self.get_token()}

        r = self.session.delete(self.pod + '/aspects/' + aspect_id,
                                data=data)

        if r.status_code != 404:
            raise Exception('wrong status code: ' + str(r.status_code))

    def get_mailbox(self):
        """This functions returns a list of messages found in the conversation.

        :returns: list -- list of Conversation objects.

        """

        data = {'authenticity_token': self.get_token()}
        r = self.session.get(self.pod + "/conversations.json")

        if r.status_code != 200:
            raise Exception('wrong status code: ' + str(r.status_code))

        mailbox = r.json()

        conversations = []

        for conversation in mailbox:
            conversations.append(diaspy.conversations.Conversation(str(conversation['conversation']['id']), self))

        return conversations

    def new_conversation(self, contacts, subject, text):
        """ start a new conversation

        :param contacts: recipients ids, no guids, comma sperated.
        :type contacts: str
        :param subject: subject of the message.
        :type subject: str
        :param text: text of the message.
        :type text: str

        """

        data = {'contact_ids': contacts,
                'conversation[subject]': subject,
                'conversation[text]': text,
                'utf8': '&#x2713;',
                'authenticity_token': self.get_token()}

        r = self.session.post(self.pod +
                                      '/conversations/',
                                      data=data,
                                      headers={'accept': 'application/json'})
        if r.status_code != 200:
            raise Exception(str(r.status_code) +
                            ': Conversation could not be started.')

        return r.json()
