const {
    AuthService,
    CredentialsValidator,
    AccessTokenGenerator,
    BasicStore,
    UserRepository,
    InvalidCredentials
} = require('../../routes/auth');

describe('#AuthService', () => {
    // should call both steps
    // should throw error if something goes wrong

})

describe('#CredentialsValidator', () => {
    // TODO encrypt the password
    const userSeed = {
        ivan: { password: '1111' }
    }

    const store = new BasicStore(userSeed);
    const userRepo = new UserRepository(store);

    const subject = new CredentialsValidator(userRepo);

    describe('given an existing user', () => {
        it('should pass given proper credentials', async () => {
            let error;
            try {
                await subject.validate('ivan', '1111');
            } catch (e) {
                error = e
            }
            expect(error).toBe(undefined)
        });

        it('should throw exception given bad credentials', async () => {
            try {
                await subject.validate('ivan', '222');
            } catch (e) {
                expect(e).toBeInstanceOf(InvalidCredentials)
            }
        });
    });

    describe('given non-existent user', () => {
        it('should throw exception given bad credentials', async () => {
            try {
                await subject.validate('nothere', '1111');
            } catch (e) {
                expect(e).toBeInstanceOf(InvalidCredentials)
            }
        });
    });
});

describe('#AuthService', () => {

    describe('given an existing user', () => {
        // TODO encrypt the password
    });
});

describe('#AuthService', () => {
    // given data
    // .  - it should build a token with the data inlined
    // given different data - it should have different hash
})