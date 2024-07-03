from bson import ObjectId
import time
class Analysis:
    def __init__(self, user_id, analysis, _id=None):
        self.user_id = user_id
        self.analysis = analysis
        self._id = _id

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data.get('user_id'),
            analysis=data.get('analysis'),
            _id=data.get('_id')
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'analysis': self.analysis
        }

    @classmethod
    def get_by_user_id(cls, mongo, user_id):
        analysis = mongo.db.analysis.find_one({'user_id': user_id})
        return cls.from_dict(analysis) if analysis else None

    def save(self, mongo):
        if self._id:
            mongo.db.analysis.update_one({'_id': self._id}, {'$set': self.to_dict()})
        else:
            self._id = mongo.db.analysis.insert_one(self.to_dict()).inserted_id