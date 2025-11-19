from .extractor import InstagramHikerApi, ThirdApiGuard


class InstagramThirdIE:
    def __init__(self, ie):
        self.ie = ie

    def extract_user_stories_info(self, username='', user_id=''):
        ThirdApiGuard.guard(self.ie, f'instagram-user-stories-{username}-{user_id}')
        return InstagramHikerApi(self.ie).extract_user_stories_info(username, user_id)

    def extract_user_highlights_info(self, username='', user_id=''):
        ThirdApiGuard.guard(self.ie, f'instagram-user-highlights-{username}-{user_id}')
        return InstagramHikerApi(self.ie).extract_user_highlights_info(username, user_id)

    def extract_user_posts_info(self, user_id='', username='', max_call_page=None):
        ThirdApiGuard.guard(self.ie, f'instagram-user-posts-{user_id}-{username}')
        return InstagramHikerApi(self.ie).extract_user_posts_info(user_id, username, max_call_page)

    def extract_post_info(self, code='', id=''):
        ThirdApiGuard.guard(self.ie, f'instagram-post-{code}-{id}')
        return InstagramHikerApi(self.ie).extract_post_info(code, id)

    def extract_story_info(self, story_id=''):
        ThirdApiGuard.guard(self.ie, f'instagram-story-{story_id}')
        return InstagramHikerApi(self.ie).extract_story_info(story_id)
