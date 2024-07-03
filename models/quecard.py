from bson import ObjectId

class Part2CueCard:
    def __init__(self, cue_card, points, _id=None):
        self.cue_card = cue_card
        self.points = points
        self._id = _id

    @classmethod
    def from_dict(cls, data):
        return cls(
            cue_card=data.get('cue_card'),
            points=data.get('points'),
            _id=data.get('_id')
        )

    def to_dict(self):
        return {
            '_id': self._id,
            'cue_card': self.cue_card,
            'points': self.points
        }

    @classmethod
    def get_all(cls, mongo):
        cue_cards = mongo.db.part2_cue_cards.find()
        return [cls.from_dict(card) for card in cue_cards]

    @classmethod
    def get_by_id(cls, mongo, card_id):
        card = mongo.db.part2_cue_cards.find_one({'_id': ObjectId(card_id)})
        return cls.from_dict(card) if card else None

    def save(self, mongo):
        if self._id:
            mongo.db.part2_cue_cards.update_one({'_id': self._id}, {'$set': self.to_dict()})
        else:
            self._id = mongo.db.part2_cue_cards.insert_one(self.to_dict()).inserted_id

    def delete(self, mongo):
        if self._id:
            mongo.db.part2_cue_cards.delete_one({'_id': self._id})

    @classmethod
    def get_random_cue_card(cls, mongo):
        pipeline = [{'$sample': {'size': 1}}]
        card = mongo.db.part2_cue_cards.aggregate(pipeline).next()
        return cls.from_dict(card)
