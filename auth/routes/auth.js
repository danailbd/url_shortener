const express = require('express');
const router = express.Router();


const default_seed = {
    ivan: { password: '1234' }
}
// TODO normal db
class BasicStore {
    #store
    constructor(seed = default_seed) {
        this.#seed(seed);
    }

    async get(key) {
        return this.#store[key];
    }

    #seed(seed) {
        this.#store = seed
    }
};

class UserRepository {
    #store
    constructor(store) {
        this.#store = store;
    }

    async findUser(username) {
        return this.#store.get(username);
    }
}

// Config
const store = new BasicStore();
const userRepo = new UserRepository(store);
// ---

class InvalidCredentials extends Error { }

// ----
const crypto = require('crypto');

// ref: https://jwt.io/
class JwtAccessTokenGenerator {
    // TODO Parameterize
    #alg = 'sha256';
    #header = {
        alg: 'HS256',
        typ: 'JWT'
    };
    // TODO move to config
    #secret = '2O1QovhnZRg0P4BbK6rh05NqvE9LBReHI5MWqrwqV44=';


    // TODO add ttl, and other claims
    // https://www.rfc-editor.org/rfc/rfc7519#section-4.1
    // https://www.iana.org/assignments/jwt/jwt.xhtml
    generate(data, ttl = 1) {
        const payload = {...data}; // TODO enhance
        const encoded_payload = this.#encodeField(payload);
        const encoded_header = this.#encodeField(this.#header);

        const signature = this.#buildSignature(this.#header, payload);

        return `${encoded_header}.${encoded_payload}.${signature}`;
    }

    #encodeField(obj) {
        return Buffer
            .from(JSON.stringify(obj))
            .toString('base64');
    }

    #buildSignature(header, payload) {
        return crypto
            .createHmac(this.#alg, Buffer.from(this.#secret, 'base64'))
            .update(`${this.#encodeField(header)}.${this.#encodeField(payload)}`)
            .digest('base64');
    }
}

// TODO: idea AuthGrantValidator
//     CredentialsValidator
//     AuthorizationCodeValidator
class CredentialsValidator {
    #userRepository

    constructor(userRepository) {
        this.#userRepository = userRepository;
    }

    async validate(username, password) {
        const user = await this.#userRepository.findUser(username);
        if (user?.password != this.#encodePassword(password)) {
            throw new InvalidCredentials;
        }
    }

    // TODO encrypt the password
    #encodePassword(password) {
        return password;
    }
}

class AuthService {
    #userRepository
    #validator
    #JwtAccessTokenGenerator

    constructor(
        userStore,
        validator = new CredentialsValidator(userStore),
        JwtAccessTokenGenerator = new JwtAccessTokenGenerator()
    ) {
        this.#userRepository = userStore;
        this.#validator = validator;
        this.#JwtAccessTokenGenerator = JwtAccessTokenGenerator;
    }

    // Throws
    async authenticate(username, password) {
        await this.#validator.validate(username, password);
        return this.#JwtAccessTokenGenerator.generate({ user: username });
    }
}

// body : { username: str, password: str}
router.post('/token', async (req, res, next) => {

    const { username, password } = req.body;

    const authService = new AuthService(userRepo);

    try {
        const result = await authService.authenticate(username, password);
    } catch (error) {
        res.status(400).json({ error: error });
        return;
    }

    res.status(200).json({ access_token: result.token });
});

module.exports = {
    router,
    AuthService,
    CredentialsValidator,
    JwtAccessTokenGenerator,
    BasicStore,
    UserRepository,
    InvalidCredentials
};
