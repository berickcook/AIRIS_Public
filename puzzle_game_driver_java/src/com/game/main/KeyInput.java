package com.game.main;

import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;

public class KeyInput extends KeyAdapter{
	
	public void keyPressed(KeyEvent e) {
		if (!Game.ai_controlled) {
			int key = e.getKeyCode();
			
			if (key == KeyEvent.VK_UP)
				Game.player_action = "Up";
			
			if (key == KeyEvent.VK_DOWN)
				Game.player_action = "Down";
			
			if (key == KeyEvent.VK_LEFT)
				Game.player_action = "Left";
			
			if (key == KeyEvent.VK_RIGHT)
				Game.player_action = "Right";
		}
	}
	
	public void keyReleased(KeyEvent e) {
		if (!Game.ai_controlled) {
			int key = e.getKeyCode();
			
			if (key == KeyEvent.VK_UP)
				if (Game.player_action == "Up")
					Game.player_action = "Nothing";
			
			if (key == KeyEvent.VK_DOWN)
				if (Game.player_action == "Down")
					Game.player_action = "Nothing";
			
			if (key == KeyEvent.VK_LEFT)
				if (Game.player_action == "Left")
					Game.player_action = "Nothing";
			
			if (key == KeyEvent.VK_RIGHT)
				if (Game.player_action == "Right")
					Game.player_action = "Nothing";
		}
	}
	
}
