#!/usr/bin/env python3

import unittest

#   failure to import any of the modules below indicates failed tests
#   modules used by diaspy
import requests
import re
#   actual diaspy code
import diaspy


####    SETUP STUFF
####    test suite configuration variables: can be adjusted to your liking
import testconf
__pod__ = testconf.__pod__
__username__ = testconf.__username__
__passwd__ = testconf.__passwd__


# Test counter
try:
    test_count_file = open('TEST_COUNT', 'r')
    test_count = int(test_count_file.read())
    test_count_file.close()
except (IOError, ValueError):
    test_count = 0
finally:
    test_count += 1
test_count_file = open('TEST_COUNT', 'w')
test_count_file.write(str(test_count))
test_count_file.close()
print('Running test no. {0}'.format(test_count))

print('Running tests on connection to pod: "{0}"\t'.format(__pod__), end='')
test_connection = diaspy.connection.Connection(pod=__pod__, username=__username__, password=__passwd__)
test_connection.login()
print('[ CONNECTED ]\n')

post_text = '#diaspy test no. {0}'.format(test_count)


#######################################
####        TEST SUITE CODE        ####
#######################################
class ConnectionTest(unittest.TestCase):
    def testLoginWithoutUsername(self):
        connection = diaspy.connection.Connection(pod=__pod__)
        self.assertRaises(diaspy.connection.LoginError, connection.login, password='foo')

    def testLoginWithoutPassword(self):
        connection = diaspy.connection.Connection(pod=__pod__)
        self.assertRaises(diaspy.connection.LoginError, connection.login, username='user')

    def testGettingUserInfo(self):
        info = test_connection.getUserInfo()
        self.assertEqual(dict, type(info))


class ClientTests(unittest.TestCase):
    def testGettingStream(self):
        client = diaspy.client.Client(test_connection)
        stream = client.get_stream()
        if len(stream): self.assertEqual(diaspy.models.Post, type(stream[0]))

    def testGettingNotifications(self):
        client = diaspy.client.Client(test_connection)
        notifications = client.get_notifications()
        self.assertEqual(list, type(notifications))
        if notifications: self.assertEqual(dict, type(notifications[0]))

    def testGettingTag(self):
        client = diaspy.client.Client(test_connection)
        tag = client.get_tag('foo')
        self.assertEqual(diaspy.streams.Generic, type(tag))
        if tag: self.assertEqual(diaspy.models.Post, type(tag[0]))

    def testGettingMailbox(self):
        client = diaspy.client.Client(test_connection)
        mailbox = client.get_mailbox()
        self.assertEqual(list, type(mailbox))
        self.assertEqual(diaspy.conversations.Conversation, type(mailbox[0]))


class StreamTest(unittest.TestCase):
    def testGetting(self):
        stream = diaspy.streams.Generic(test_connection)

    def testGettingLength(self):
        stream = diaspy.streams.Generic(test_connection)
        len(stream)

    def testClearing(self):
        stream = diaspy.streams.Stream(test_connection)
        stream.clear()
        self.assertEqual(0, len(stream))

    def testPurging(self):
        stream = diaspy.streams.Stream(test_connection)
        post = stream.post('#diaspy test')
        stream.update()
        post.delete()
        stream.purge()
        self.assertNotIn(post.post_id, [p.post_id for p in stream])

    def testPostingText(self):
        stream = diaspy.streams.Stream(test_connection)
        post = stream.post(post_text)
        self.assertEqual(diaspy.models.Post, type(post))
    
    @unittest.skip('returns internal server error -- not our fault that it is failing')
    def testPostingImage(self):
        stream = diaspy.streams.Stream(test_connection)
        stream.post(text=post_text, photo='test-image.png')

    def testingAddingTag(self):
        ft = diaspy.streams.FollowedTags(test_connection)
        ft.add('test')

    def testAspectsAdd(self):
        aspects = diaspy.streams.Aspects(test_connection)
        aspects.add(testconf.test_aspect_name_fake)
        testconf.test_aspect_id = aspects.add(testconf.test_aspect_name)

    def testAspectsGettingID(self):
        aspects = diaspy.streams.Aspects(test_connection)
        id = aspects.getAspectID(testconf.test_aspect_name)
        self.assertEqual(testconf.test_aspect_id, id)

    def testAspectsRemoveById(self):
        aspects = diaspy.streams.Aspects(test_connection)
        aspects.remove(testconf.test_aspect_id)
        self.assertEqual(-1, aspects.getAspectID(testconf.test_aspect_name))

    def testAspectsRemoveByName(self):
        aspects = diaspy.streams.Aspects(test_connection)
        aspects.remove(name=testconf.test_aspect_name_fake)
        self.assertEqual(-1, aspects.getAspectID(testconf.test_aspect_name_fake))

    def testActivity(self):
        activity = diaspy.streams.Activity(test_connection)

    def testMentionsStream(self):
        mentions = diaspy.streams.Mentions(test_connection)


class UserTests(unittest.TestCase):
    def testHandleSeparatorRaisingExceptions(self):
        user = diaspy.people.User(test_connection)
        handles = ['user.pod.example.com',
                   'user@podexamplecom',
                   '@pod.example.com',
                   'use r@pod.example.com',
                   'user0@pod300 example.com',
                   ]
        for h in handles:
            self.assertRaises(Exception, user._sephandle, h)

    def testGettingUserByHandle(self):
        user = diaspy.people.User(test_connection)
        user.fetchhandle(testconf.diaspora_id)
        self.assertEqual(testconf.guid, user['guid'])
        self.assertEqual(testconf.diaspora_name, user['diaspora_name'])
        self.assertIn('id', user.data)
        self.assertIn('image_urls', user.data)
        self.assertEqual(type(user.stream), diaspy.streams.Outer)

    def testGettingUserByGUID(self):
        user = diaspy.people.User(test_connection)
        user.fetchguid(testconf.guid)
        self.assertEqual(testconf.diaspora_id, user['diaspora_id'])
        self.assertEqual(testconf.diaspora_name, user['diaspora_name'])
        self.assertIn('id', user.data)
        self.assertIn('image_urls', user.data)
        self.assertEqual(type(user.stream), diaspy.streams.Outer)


class ContactsTest(unittest.TestCase):
    def testGetOnlySharing(self):
        contacts = diaspy.people.Contacts(test_connection)
        only_sharing = contacts.get_only_sharing()
        for i in only_sharing:
            self.assertEqual(diaspy.people.User, type(i))

    def testGetAll(self):
        contacts = diaspy.people.Contacts(test_connection)
        only_sharing = contacts.get_all()
        for i in only_sharing:
            self.assertEqual(diaspy.people.User, type(i))

    def testGet(self):
        contacts = diaspy.people.Contacts(test_connection)
        only_sharing = contacts.get()
        for i in only_sharing:
            self.assertEqual(diaspy.people.User, type(i))


class PostTests(unittest.TestCase):
    def testStringConversion(self):
        s = diaspy.streams.Stream(test_connection)

    def testRepr(self):
        s = diaspy.streams.Stream(test_connection)


if __name__ == '__main__': unittest.main()
