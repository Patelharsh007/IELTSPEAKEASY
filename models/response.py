from bson import ObjectId
from datetime import datetime

class Response:
    def __init__(self, user_id, exam_session_id, basic_questions=None, part1_questions=None,
                 part2_cue_card=None, part3_answers=None, timestamp=None, _id=None,
                 scores=None, band_scores=None, overall_evaluation='', overall_band=0):
        self._id = _id if _id else ObjectId()
        self.user_id = user_id
        self.exam_session_id = exam_session_id
        self.basic_questions = basic_questions if basic_questions else []
        self.part1_questions = part1_questions if part1_questions else []
        self.part2_cue_card = part2_cue_card if part2_cue_card else {}
        self.part3_answers = part3_answers if part3_answers else []
        self.timestamp = timestamp if timestamp else datetime.now()
        self.scores = scores if scores else {}
        self.band_scores = band_scores if band_scores else {}
        self.overall_evaluation = overall_evaluation
        self.overall_band = overall_band

    @classmethod
    def get_by_session_id(cls, mongo, session_id):
        response_data = mongo.db.responses.find_one({'exam_session_id': session_id})
        return cls.from_dict(response_data) if response_data else None

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data.get('user_id'),
            exam_session_id=data.get('exam_session_id'),
            basic_questions=data.get('basic_questions'),
            part1_questions=data.get('part1_questions'),
            part2_cue_card=data.get('part2_cue_card'),
            part3_answers=data.get('part3_answers'),
            timestamp=data.get('timestamp'),
            _id=data.get('_id'),
            scores=data.get('scores'),
            band_scores=data.get('band_scores'),
            overall_evaluation=data.get('overall_evaluation'),
            overall_band=data.get('overall_band')
        )

    def update_part1_questions(self, mongo, part1_questions):
        mongo.db.responses.update_one(
            {'_id': self._id},
            {'$set': {'part1_questions': part1_questions}}
        )
        self.part1_questions = part1_questions

    def save(self, mongo):
        collection = mongo.db.responses
        collection.update_one(
            {'_id': self._id},
            {'$set': self.to_dict()},
            upsert=True
        )

    def to_dict(self):
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'exam_session_id': self.exam_session_id,
            'basic_questions': self.basic_questions,
            'part1_questions': self.part1_questions,
            'part2_cue_card': self.part2_cue_card,
            'part3_answers': self.part3_answers,
            'timestamp': self.timestamp,
            'scores': self.scores,
            'band_scores': self.band_scores,
            'overall_evaluation': self.overall_evaluation,
            'overall_band': self.overall_band
        }

    def update_scores(self, mongo, scores):
        mongo.db.responses.update_one(
            {'_id': self._id},
            {'$set': {'scores': scores}}
        )
        self.scores = scores

    def update_band_scores(self, mongo, band_scores):
        mongo.db.responses.update_one(
            {'_id': self._id},
            {'$set': {'band_scores': band_scores}}
        )
        self.band_scores = band_scores

    def update_overall_evaluation(self, mongo, overall_evaluation):
        mongo.db.responses.update_one(
            {'_id': self._id},
            {'$set': {'overall_evaluation': overall_evaluation}}
        )
        self.overall_evaluation = overall_evaluation

    def update_overall_band(self, mongo, overall_band):
        mongo.db.responses.update_one(
            {'_id': self._id},
            {'$set': {'overall_band': overall_band}}
        )
        self.overall_band = overall_band
