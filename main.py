from enum import Enum

class Player():
    def __init__(self, name: str, origin: str, level: int, height: int):
        self.name = name
        self.origin = origin
        self.level = level
        self.height = height



class MoodState(Enum):
    GOOD = 1
    FINE = 2
    NOT_GREAT = 3
    BAD = 4


class MentalState(Enum):
    EXHAUSTED = 1
    STRESSED = 2
    NEUTRAL = 3
    CALM = 4
    MOTIVATED = 5

MOOD_POINTS = {
    MoodState.GOOD: 35,
    MoodState.FINE: 25,
    MoodState.NOT_GREAT: 10,
    MoodState.BAD: 0,
}

MENTAL_POINTS = {
    MentalState.EXHAUSTED: 0,
    MentalState.STRESSED: 10,
    MentalState.NEUTRAL: 20,
    MentalState.CALM: 30,
    MentalState.MOTIVATED: 35,
}


def is_focused(study_time, sleep_time, mental_state: MentalState, screen_time):
    if mental_state == MentalState.EXHAUSTED:
        return False  # deal-breaker, no need to go further

    score = MENTAL_POINTS[mental_state]
    score += min(sleep_time / 8, 1) * 35
    score += max(1 - screen_time / 6, 0) * 20
    score += min(study_time / 2, 1) * 10
    return score >= 60


def is_happy(social_time: float, stress_level: int, mood: MoodState, did_something_fun: bool) -> bool:
    if mood == MoodState.BAD:
        return False

    score = MOOD_POINTS[mood]
    score += min(social_time / 2, 1) * 25
    score += (10 - stress_level) / 10 * 25
    score += 15 if did_something_fun else 0
    return score >= 60
