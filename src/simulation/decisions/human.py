from src.plots.plot import Plot
from src.simulation.decisions.decision_maker import DecisionMaker
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size
from src.utils.criteria import Criteria


class HumanPlayer(DecisionMaker):
    def __init__(self):
        super().__init__()

    def get_action(self, possible_actions):

        action_chose = None
        while action_chose is None:
            print('You have to choose an action')
            for i, act in enumerate(possible_actions):
                print(f'{i} - {act}')

            try:
                action_chose = possible_actions[int(input('Selected : '))]
            except IndexError:
                print('Your answer is incorrect')
            except ValueError:
                print('Your answer is incorrect')
        return action_chose

    def get_coordinates(self, plot: Plot, size: Size):
        plot = Plot(*plot.start, size=plot.size - size)
        print(f"Choose coordinates between {plot.start} and {plot.end}")
        coord = None
        while coord is None:
            answer = input("Coordinates for the building X Z: ").split()
            try:
                x, z = int(answer[0]), int(answer[1])
                coord = Coordinates(x, 0, z)
                coord = plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(coord).coordinates
            except Exception:
                print("Something went wrong with your coordinate")

            if coord and coord not in plot:
                print(f"Coord {coord} not in plot !")
                coord = None
        return coord

    def get_rotation(self):
        angles = [0, 90, 180, 270]
        print(f"Choose rotation between {angles}")
        rotation = None
        while rotation is None:
            for i, ang in enumerate(angles):
                print(f'{i} - {ang}')
            try:
                rotation = angles[int(input('Selected : '))]
            except IndexError:
                print('Your answer is incorrect')
            except ValueError:
                print('Your answer is incorrect')
        return rotation
