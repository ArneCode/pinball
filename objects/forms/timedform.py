from collision.collision import TimedCollision
from math_utils.vec import Vec
from objects.form import Form


class TimedForm(Form):
    """
    A wrapper auround a form that makes it measure time relative to a given start time.
    
    Attributes:
        - form (Form): The form
        - start_time (float): The start time
        - name (str): The name of the form
    """
    form: Form
    start_time: float
    name: str

    def __init__(self, form: Form, start_time: float, name="timedform"):
        """
        Initialize the TimedForm
        
        Args:
            - form: The form
            - start_time: The start time
            - name: The name of the form
        """
        self.form = form
        self.start_time = start_time
        self.name = name

    def draw(self, screen, color, time: float):
        """
        Draw the form on the screen
        
        Args:
            - screen: The screen to draw on
            - color: The color to use for drawing
            - time: The current time
        """
        self.form.draw(screen, color, time-self.start_time)

    def find_collision(self, ball):
        """
        Find the first collision of the ball with the form
        
        Args:
            - ball: The ball to check for collision
        
        Returns:
            - TimedCollision: The first collision of the ball with the form
        """
        if self.start_time > ball.start_t:
            ball_pos = ball.get_pos(self.start_time)
            ball_vel = ball.get_vel(self.start_time)

            timed_ball = ball.with_start_pos(ball_pos).with_vel(ball_vel).with_start_t(0.0)
        else:
            timed_ball = ball.with_start_t(ball.start_t - self.start_time)
        coll = self.form.find_collision(timed_ball)

        if coll is None:
            return None
        
        coll_t = coll.get_coll_t() + self.start_time + timed_ball.start_t
        #raise Exception(f"coll_t: {coll_t}, coll: {coll}, ball.start_t: {ball.start_t}")
        print(f"TimedForm coll_t: {coll_t - ball.start_t}, coll: {coll}, ball.start_t: {ball.start_t}, self_start_t: {self.start_time}")
        return TimedCollision(coll, coll_t - ball.start_t)
    def is_moving(self, t: float) -> bool:
        return self.form.is_moving(t - self.start_time)
    
    def get_name(self) -> str:
        return self.name
    
    def get_material(self):
        return self.form.get_material()
    
    def get_points(self, time: float):
        return self.form.get_points(time-self.start_time)
    
    def get_json(self) -> dict:
        return {
            "type": "TimedForm",
            "params": {
                "form": self.form.get_json(),
                "start_time": self.start_time,
                "name": self.name
            }
        }
    def rotate(self, angle: float, center: Vec[float]) -> Form:
        return TimedForm(self.form.rotate(angle, center), self.start_time, self.name)