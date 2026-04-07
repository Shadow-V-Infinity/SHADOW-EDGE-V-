def get_player_clips(self, player_id, limit=10):
    """
    Retourne les clips vidéo du joueur (via PBP + video scraper)
    """
    try:
        clips = self.pbp.get_player_clips(player_id)
        return clips[:limit]
    except:
        return []
