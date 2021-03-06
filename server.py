#!/usr/bin/env python3

import os

import cleancss
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.web

from config import web as config
import github

class BaseHandler(tornado.web.RequestHandler):
	def render(self, *args, **kwargs):
		kwargs['host'] = config.host
		return super(BaseHandler, self).render(*args, **kwargs)

	def render_string(self, *args, **kwargs):
		s = super(BaseHandler, self).render_string(*args, **kwargs)
		return s.replace(b'\n', b'') # this is like Django's {% spaceless %}

class MainHandler(BaseHandler):
	def get(self):
		self.render('home.html')

class LoginHandler(BaseHandler, github.GithubMixin):
	@tornado.gen.coroutine
	def get(self):
		if self.get_argument('code', False):
			user = yield self.get_authenticated_user(
				redirect_uri=config.host + '/github_oauth',
				code=self.get_argument('code'),
			)
			self.set_secure_cookie('access_token', user['access_token'])
			self.redirect('/')
		else:
			self.authorize_redirect(
				redirect_uri=config.host + '/github_oauth',
				scope=['user:email'],
			)

class CSSHandler(tornado.web.RequestHandler):
	def get(self, css_path):
		css_path = os.path.join(os.path.dirname(__file__), 'static', css_path) + '.ccss'
		with open(css_path, 'r') as f:
			self.set_header('Content-Type', 'text/css')
			self.write(cleancss.convert(f))

if __name__ == '__main__':
	tornado.web.Application(
		handlers=[
			(r'/', MainHandler),
			(r'/github_oauth', LoginHandler),
			(r'/(css/.+)\.css', CSSHandler),
		],
		template_path=os.path.join(os.path.dirname(__file__), 'templates'),
		static_path=os.path.join(os.path.dirname(__file__), 'static'),
		cookie_secret=config.cookie_secret,
		debug=config.debug,
	).listen(config.port)
	print('listening on :%d' % config.port)
	tornado.ioloop.IOLoop.instance().start()
