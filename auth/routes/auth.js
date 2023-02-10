const express = require('express');
const router = express.Router();


const default_seed = {
    ivan: { password: '1234' }
}
// TODO normal db
class BasicStore {
    #store
    constructor(seed=default_seed) {
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

// ref: https://jwt.io/
class AccessTokenGenerator {
    generate(payload) {
        // TODO
        const data = { ...payload };
        const alg = {
            typ: 'JWT',
            alg: 'HS256'
        }
        //  HMACSHA256(
        //     base64UrlEncode(header) + "." +
        //     base64UrlEncode(payload),

        //   your-256-bit-secret

        //   )
        return data
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
    #accessTokenGenerator

    constructor(
        userStore,
        validator = new CredentialsValidator(userStore),
        accessTokenGenerator = new AccessTokenGenerator()
    ) {
        this.#userRepository = userStore;
        this.#validator = validator;
        this.#accessTokenGenerator = accessTokenGenerator;
    }

    // Throws
    async authenticate(username, password) {
        await this.#validator.validate(username, password);
        return await this.#accessTokenGenerator.generate(username)
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
    AccessTokenGenerator,
    BasicStore,
    UserRepository,
    InvalidCredentials
};
