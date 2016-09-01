from pgoapi import PGoApi
from location import get_route, get_increments
import logging, time, math
from _pytest.config import Config
from pgoapi.pgoapi import PGoApi


class ApiWrapper(PGoApi):
    def __init__(self, args):
        PGoApi.__init__(self)
        self.args = args
        self.config = {}
        self.config['GMAPS_API_KEY'] = args.gmaps_key
        self.config['USE_GOOGLE'] = False
        
    def calc_distance(self, to):
        loc_from = self._position_lng
        loc_to = to
        R = 6378.1  # km radius of the earth
    
        dLat = math.radians(loc_from[0] - loc_to[0])
        dLon = math.radians(loc_from[1] - loc_to[1])
    
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
            math.cos(math.radians(loc_from[0])) * math.cos(math.radians(loc_to[0])) * \
            math.sin(dLon / 2) * math.sin(dLon / 2)
    
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = R * c
    
        return d

    def walk_to(self, loc, speed=100):
        steps = get_route(self._posf, loc, self.config.get("USE_GOOGLE", False), self.config.get("GMAPS_API_KEY", ""))
        for step in steps:
            for i, next_point in enumerate(get_increments(self._posf, step, speed)):
                self.set_position(*next_point)
                logging.info("Walking at position {lat},{lon}".format(lat=self._position_lat,
                                                                       lon=self._position_lng))
                time.sleep(2) # If you want to make it faster, delete this line... would not recommend though
        pass

    
    def attempt_catch(self, encounter_id, spawn_point_guid): #Problem here... add 4 if you have master ball
        for i in range(1,3): # Range 1...4 iff you have master ball `range(1,4)`
            r = self.catch_pokemon(
                normalized_reticle_size=1.950,
                pokeball=i,
                spin_modifier=0.850,
                hit_pokemon=True,
                normalized_hit_position=1,
                encounter_id=encounter_id,
                spawn_point_id=spawn_point_guid,
                )['responses']['CATCH_POKEMON']
            if "status" in r:
                return r
    
    def encounter_pokemon(self, pokemon):
        encounter_id = pokemon['encounter_id']
        spawn_point_id = pokemon['spawn_point_id']
        position = self._posf
        encounter = self.encounter(encounter_id=encounter_id,
                                   spawn_point_id=spawn_point_id,
                                   player_latitude=position[0],
                                   player_longitude=position[1])['responses']['ENCOUNTER']
        self.log.debug("Started Encounter: %s", encounter)
        if encounter['status'] == 1:
            capture_status = -1
            limit = 5
            while capture_status != 0 and capture_status != 3:
                count = 1
                catch_attempt = self.attempt_catch(encounter_id, spawn_point_id)
                capture_status = catch_attempt['status']
                if capture_status in (1, 3):
                    time.sleep(5) # If you want to make it faster, delete this line... would not recommend though
                    return catch_attempt

                # Only try up to x attempts
                count += 1
                if count >= limit:
                    logging.info("Over catch limit")
                    return 100 + count

                time.sleep(5) # If you want to make it faster, delete this line... would not recommend though
        return False