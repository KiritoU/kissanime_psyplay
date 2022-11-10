import logging

from _db import database
from helper import helper
from settings import CONFIG

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


class PsyPlay:
    def __init__(self, film: dict, episodes: dict):
        self.film = film
        self.film["quality"] = (
            "HD"
            if "Quality" not in self.film["extra_info"].keys()
            else self.film["extra_info"]["Quality"]
        )
        self.episodes = episodes

    def insert_movie_details(self, post_id):
        if not self.episodes:
            return

        logging.info("Inserting movie players")

        episodes_keys = list(self.episodes.keys())
        episode_number = episodes_keys[0]
        episode = self.episodes[episode_number]
        players = helper.get_players_iframes(episode["links"])
        postmeta_data = [
            (post_id, "player", str(len(players))),
            (post_id, "_player", "field_5640ccb223222"),
        ]
        postmeta_data.extend(
            helper.generate_players_postmeta_data(
                post_id, players, self.film["quality"]
            )
        )

        helper.insert_postmeta(postmeta_data)

    def insert_root_film(self) -> list:
        condition_post_title = self.film["post_title"].replace("'", "''")
        condition = f"""post_title = '{condition_post_title}' AND post_type='{self.film["post_type"]}'"""
        be_post = database.select_all_from(
            table=f"{CONFIG.TABLE_PREFIX}posts", condition=condition
        )
        if not be_post:
            logging.info(f'Inserting root film: {self.film["post_title"]}')
            post_data = helper.generate_film_data(
                self.film["post_title"],
                self.film["description"],
                self.film["post_type"],
                self.film["trailer_id"],
                self.film["fondo_player"],
                self.film["poster_url"],
                self.film["extra_info"],
                self.film["status"],
            )

            return [helper.insert_film(post_data), True]
        else:
            return [be_post[0][0], False]

    def insert_episodes(self, post_id):
        self.episodes.reverse()
        lenEpisodes = len(self.episodes)
        for i in range(lenEpisodes):
            episode = self.episodes[i]
            episode_title = episode["title"]

            condition_episode_title = episode_title.replace("'", "''")
            condition = f'post_title = "{condition_episode_title}"'
            be_post = database.select_all_from(
                table=f"{CONFIG.TABLE_PREFIX}posts", condition=condition
            )
            if be_post:
                continue

            logging.info(f"Inserting episode: {episode_title}")

            episode_data = helper.generate_episode_data(
                post_id,
                episode_title,
                self.film["season_number"],
                i,
                self.film["post_title"],
                self.film["fondo_player"],
                self.film["poster_url"],
                self.film["quality"],
                episode["links"],
            )

            helper.insert_episode(episode_data)

    def insert_film(self):
        (
            self.film["post_title"],
            self.film["season_number"],
        ) = helper.get_title_and_season_number(self.film["title"])

        if len(self.episodes) > 1:
            self.film["post_type"] = "tvshows"

        post_id, isNewPostInserted = self.insert_root_film()

        if self.film["post_type"] != "tvshows":
            if isNewPostInserted:
                self.insert_movie_details(post_id)
        else:
            self.insert_episodes(post_id)
