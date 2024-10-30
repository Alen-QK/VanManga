from faker import Faker

def ua_producer():
    UA = Faker()

    return UA.user_agent()