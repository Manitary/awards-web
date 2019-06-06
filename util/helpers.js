const {STATUS_CODES} = require('http');
const superagent = require('superagent');
const log = require('another-logger');
const config = require('../config');
const r = require('./db');

const requestHelpers = {
	reddit () {
		const originalRequest = this;
		let accessToken = originalRequest.session.redditAccessToken;
		const refreshToken = originalRequest.session.redditRefreshToken;
		// Function to send a request and handle token expiry automatically.
		// The return value of this function can be handled just like if you
		// called `superagent.get(...)` normally.
		function sendRequest (method, path, retried = false) {
			// Try to send the request with the stored access token...
			return superagent[method.toLowerCase()](`https://oauth.reddit.com${path}`)
				.set('Authorization', `bearer ${accessToken}`)
				.catch(async ({response}) => {
					// If we've already tried to get a new token once, don't do
					// the same thing again - chances are it's not our error.
					// We also can't do anything if we don't have a refresh
					// token for whatever reason.
					if (retried || !refreshToken) {
						throw response;
					}
					// Try to get a new access token via the stored token
					const refreshResponse = await superagent
						.post('https://www.reddit.com/api/v1/access_token')
						.auth(config.reddit.clientId, config.reddit.clientSecret)
						.query({
							grant_type: 'refresh_token',
							refresh_token: refreshToken,
						});
					// Did we get an error? If so then give up
					if (refreshResponse.body.error) throw refreshResponse;
					// Change the access token for the next request
					accessToken = refreshResponse.body.access_token;
					// Also set it in the session for all future requests
					originalRequest.session.redditAccessToken = accessToken;
					// And retry the request, marking that this is a retry
					return sendRequest(method, path, true);
				});
		}
		// Instead of having to pass method to the function, we get fancy and
		// bind all HTTP verbs to the function so we can do `.reddit.get(...)`
		// instead of `.reddit('GET', ...)`.
		const obj = {};
		[
			'get',
			'head',
			'patch',
			'options',
			'connect',
			'delete',
			'trace',
			'post',
			'put',
		].forEach(verb => {
			obj[verb] = sendRequest.bind(null, verb);
		});
		// we also have the method-first one if we want that
		obj.sendRequest = sendRequest;
		return obj;
	},
	body () {
		return new Promise(resolve => {
			const chunks = [];
			this.on('data', chunk => {
				chunks.push(chunk);
			}).on('end', () => {
				resolve(Buffer.concat(chunks).toString());
			});
		});
	},
	json () {
		return this.body().then(body => JSON.parse(body));
	},
	async authenticate ({level}) {
		const redditInfo = (await this.reddit().get('/api/v1/me')).body;
		const userInfo = (await r.table('users').filter({reddit: redditInfo.name}).run())[0];
		log.debug('target level', level);
		log.debug('actual level', userInfo.level);
		if (level && userInfo.level < level) return false;
		return true;
	},
};
const responseHelpers = {
	json (status = 200, data) {
		if (typeof status !== 'number') {
			data = status;
			status = 200;
		} else if (data === undefined) {
			data = {status, message: STATUS_CODES[status]};
		}
		this.writeHead(status, {
			'Content-Type': 'application/json',
		});
		this.end(JSON.stringify(data));
	},
	redirect (status = 302, location) {
		if (typeof status !== 'number') {
			location = status;
			status = 302;
		}
		this.writeHead(status, {
			Location: location,
		});
		this.end();
	},
};

module.exports = (request, response, next) => {
	Object.assign(request, requestHelpers);
	Object.assign(response, responseHelpers);
	next();
};
