package com.game.main;

import java.awt.Canvas;
import java.awt.Color;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.image.BufferStrategy;
import java.io.File;
import java.io.IOException;

import javax.imageio.ImageIO;

public class Game extends Canvas implements Runnable{
	
	private static final long serialVersionUID = -6680875776510531796L;
	
	// width and height of game window is 640 x 480. Padded numbers to account for the window border cause I couldn't get .pack() to work
	public static final int WIDTH = 646, HEIGHT = 508;
	
	private Thread thread;
	private boolean running = false;
	
	// These are the arrays to pass to the AI 
	public static int[][] screen_input = new int[20][15];
	public static int[][] aux_input = new int[1][2];
	
	// This toggles whether a human player or an AI is in control of the game
	public static boolean ai_controlled = false;

	// This is the action to be performed in the next step. The available actions are: "Up", "Down", "Left", "Right", "Nothing"
	public static String player_action = "Nothing";
	
	// Game variables
	public static int loc_prev = 0;
	public static int player_x = 0;
	public static int player_y = 0;
	public static int battery_count = 0;
	public static int level = 0;
	
	public Game() {
		this.addKeyListener(new KeyInput());
		new Window(WIDTH, HEIGHT, "Puzzle Game", this);
	}
	
	// These 3 blocks are needed because reasons
	public synchronized void start() {
		thread = new Thread(this);
		thread.start();
		running = true;
	}
	
	public synchronized void stop() {
		try {
			thread.join();
			running = false;
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	public static void main(String args[]) {
		new Game();
	}

	// Game initialization and loop
	public void run() {
		
		// Set all grid values to 0 (empty floor)
		for (int i = 0; i < 20 ; i++) {
			for (int j = 0; j < 15; j++)
				screen_input[i][j] = 0;
		}
		
//		All possible grid values and what they represent
//		
//		----------------------------------------------------
//		id   Object
//		----------------------------------------------------
//		0    floor
//		1    character
//		2    wall
//		3    battery
//		4    door
//		5    key
//		6    fire extinguisher
//		7    fire
//		8    1 way arrow right
//		9    1 way arrow left
//		10   1 way arrow down
//		11   1 way arrow up
//		12   open door
//		13   player character standing on top of right arrow
//		14   player character standing on top of left arrow
//		15   player character standing on top of down arrow
//		16   player character standing on top of up arrow
//		17   player character standing in open door
//		----------------------------------------------------

		// Keys Collected
		aux_input[0][0] = 0;
		// Fire Extinguishers Collected
		aux_input[0][1] = 0;
		
		// Load game sprites
		Image[] sprites = new Image[13];
		
		try {
			sprites[0] = ImageIO.read(new File("FloorS_0.png"));
			sprites[1] = ImageIO.read(new File("CharS_0.png"));
			sprites[2] = ImageIO.read(new File("WallS_0.png"));
			sprites[3] = ImageIO.read(new File("BatteryS_0.png"));
			sprites[4] = ImageIO.read(new File("DoorS_0.png"));
			sprites[5] = ImageIO.read(new File("KeyS_0.png"));
			sprites[6] = ImageIO.read(new File("ExtinguishS_0.png"));
			sprites[7] = ImageIO.read(new File("FireS_0.png"));
			sprites[8] = ImageIO.read(new File("ArrowRS_0.png"));
			sprites[9] = ImageIO.read(new File("ArrowLS_0.png"));
			sprites[10] = ImageIO.read(new File("ArrowDS_0.png"));
			sprites[11] = ImageIO.read(new File("ArrowUS_0.png"));
			sprites[12] = ImageIO.read(new File("DoorOpenS_0.png"));
		} catch (IOException e) {
			e.printStackTrace();
		}
		
		// Load first level
		loadLevel();
		
		// Game loop
		while (running) {
			
			if (ai_controlled) {
				
				/* 
				 * 
				 * AI code goes here. 
				 * Pass current screen_input and aux_input to your AI
				 * and return a player_action (up, down, left, right, or nothing)
				 * 
				*/
				
			}
			
			// Handles game logic
			handler(player_action);
			
			// Renders the screen
			render(sprites);
			
			/*
			*
			* Optional AI code goes here. Send the updated screen_input and aux_input to your AI
			* to learn from.
			*
			*/
			
			// Controls frame rate. Comment out to maximize speed for AI.
			try {
				Thread.sleep(100);
			} catch (InterruptedException e) {
				e.printStackTrace();
			}
		}
		stop();
	}
	
	// Game logic
	private void handler(String action) {
		if (action == "Up") {
			if (player_y > 0) {
				int look = screen_input[player_x][player_y-1];
				
				switch(look) {
					case 0:
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = screen_input[player_x][player_y];
						screen_input[player_x][player_y] = 1;
						break;
					case 3:
						battery_count -= 1;
						if (battery_count == 0) {
							level += 1;
							if (level > 11)
								level = 0;
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						else {
							screen_input[player_x][player_y] = loc_prev;
							player_y -= 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						break;
					case 4:
						if (aux_input[0][0] > 0) {
							aux_input[0][0] -= 1;
							screen_input[player_x][player_y-1] = 12;
						}
						break;
					case 5:
						aux_input[0][0] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 6:
						aux_input[0][1] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 7:
						if (aux_input[0][1] > 0) {
							aux_input[0][1] -= 1;
							screen_input[player_x][player_y] = loc_prev;
							player_y -= 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						else {
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						break;
					case 8:
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = 8;
						screen_input[player_x][player_y] = 13;
						break;
					case 9:
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = 9;
						screen_input[player_x][player_y] = 14;
						break;
					case 11:
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = 11;
						screen_input[player_x][player_y] = 16;
						break;
					case 12:
						screen_input[player_x][player_y] = loc_prev;
						player_y -= 1;
						loc_prev = 12;
						screen_input[player_x][player_y] = 17;
						break;
				}
			}
		}
		
		if (action == "Down") {
			if (player_y < 14) {
				int look = screen_input[player_x][player_y+1];
				
				switch(look) {
					case 0:
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = screen_input[player_x][player_y];
						screen_input[player_x][player_y] = 1;
						break;
					case 3:
						battery_count -= 1;
						if (battery_count == 0) {
							level += 1;
							if (level > 11)
								level = 0;
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						else {
							screen_input[player_x][player_y] = loc_prev;
							player_y += 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						break;
					case 4:
						if (aux_input[0][0] > 0) {
							aux_input[0][0] -= 1;
							screen_input[player_x][player_y+1] = 12;
						}
						break;
					case 5:
						aux_input[0][0] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 6:
						aux_input[0][1] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 7:
						if (aux_input[0][1] > 0) {
							aux_input[0][1] -= 1;
							screen_input[player_x][player_y] = loc_prev;
							player_y += 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						else {
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						break;
					case 8:
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = 8;
						screen_input[player_x][player_y] = 13;
						break;
					case 9:
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = 9;
						screen_input[player_x][player_y] = 14;
						break;
					case 10:
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = 10;
						screen_input[player_x][player_y] = 15;
						break;
					case 12:
						screen_input[player_x][player_y] = loc_prev;
						player_y += 1;
						loc_prev = 12;
						screen_input[player_x][player_y] = 17;
						break;
				}
			}		
		}
		
		if (action == "Left") {
			if (player_x > 0) {
				int look = screen_input[player_x-1][player_y];
				
				switch(look) {
					case 0:
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = screen_input[player_x][player_y];
						screen_input[player_x][player_y] = 1;
						break;
					case 3:
						battery_count -= 1;
						if (battery_count == 0) {
							level += 1;
							if (level > 11)
								level = 0;
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						else {
							screen_input[player_x][player_y] = loc_prev;
							player_x -= 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						break;
					case 4:
						if (aux_input[0][0] > 0) {
							aux_input[0][0] -= 1;
							screen_input[player_x-1][player_y] = 12;
						}
						break;
					case 5:
						aux_input[0][0] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 6:
						aux_input[0][1] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 7:
						if (aux_input[0][1] > 0) {
							aux_input[0][1] -= 1;
							screen_input[player_x][player_y] = loc_prev;
							player_x -= 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						else {
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						break;
					case 11:
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = 11;
						screen_input[player_x][player_y] = 16;
						break;
					case 9:
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = 9;
						screen_input[player_x][player_y] = 14;
						break;
					case 10:
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = 10;
						screen_input[player_x][player_y] = 15;
						break;
					case 12:
						screen_input[player_x][player_y] = loc_prev;
						player_x -= 1;
						loc_prev = 12;
						screen_input[player_x][player_y] = 17;
						break;
				}
			}
		}
		
		if (action == "Right") {
			if (player_x < 19) {
				int look = screen_input[player_x+1][player_y];
				
				switch(look) {
					case 0:
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = screen_input[player_x][player_y];
						screen_input[player_x][player_y] = 1;
						break;
					case 3:
						battery_count -= 1;
						if (battery_count == 0) {
							level += 1;
							if (level > 11)
								level = 0;
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						else {
							screen_input[player_x][player_y] = loc_prev;
							player_x += 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						break;
					case 4:
						if (aux_input[0][0] > 0) {
							aux_input[0][0] -= 1;
							screen_input[player_x+1][player_y] = 12;
						}
						break;
					case 5:
						aux_input[0][0] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 6:
						aux_input[0][1] += 1;
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = 0;
						screen_input[player_x][player_y] = 1;
						break;
					case 7:
						if (aux_input[0][1] > 0) {
							aux_input[0][1] -= 1;
							screen_input[player_x][player_y] = loc_prev;
							player_x += 1;
							loc_prev = 0;
							screen_input[player_x][player_y] = 1;
						}
						else {
							screen_input[player_x][player_y] = 0;
							loc_prev = 0;
							loadLevel();
						}
						break;
					case 11:
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = 11;
						screen_input[player_x][player_y] = 16;
						break;
					case 8:
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = 8;
						screen_input[player_x][player_y] = 13;
						break;
					case 10:
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = 10;
						screen_input[player_x][player_y] = 15;
						break;
					case 12:
						screen_input[player_x][player_y] = loc_prev;
						player_x += 1;
						loc_prev = 12;
						screen_input[player_x][player_y] = 17;
						break;
				}
			}		
		}
	}
	
	// Level data
	private void loadLevel() {
		
		for (int i = 0; i < 20 ; i++) {
			for (int j = 0; j < 15; j++)
				screen_input[i][j] = 0;
		}
		
		switch(level) {
			case 0:
				screen_input[4][2] = 2;
				screen_input[4][3] = 2;
				screen_input[4][4] = 2;
				screen_input[4][5] = 2;
				screen_input[4][6] = 2;
				screen_input[4][7] = 2;
				screen_input[4][8] = 2;
				screen_input[4][9] = 2;
				screen_input[4][10] = 2;
				screen_input[4][11] = 2;
				screen_input[4][12] = 2;
				screen_input[5][2] = 2;
				screen_input[5][8] = 2;
				screen_input[5][12] = 2;
				screen_input[6][2] = 2;
				screen_input[6][10] = 3;
				screen_input[6][12] = 2;
				screen_input[7][2] = 2;
				screen_input[7][5] = 2;
				screen_input[7][8] = 2;
				screen_input[7][12] = 2;
				screen_input[8][2] = 2;
				screen_input[8][5] = 2;
				screen_input[8][8] = 2;
				screen_input[8][9] = 2;
				screen_input[8][10] = 2;
				screen_input[8][11] = 2;
				screen_input[8][12] = 2;
				screen_input[9][2] = 2;
				screen_input[9][5] = 2;
				screen_input[9][8] = 2;
				screen_input[9][12] = 2;
				screen_input[10][2] = 2;
				screen_input[10][5] = 2;
				screen_input[10][10] = 1;
				player_x = 10;
				player_y = 10;
				screen_input[10][12] = 2;
				screen_input[11][2] = 2;
				screen_input[11][5] = 2;
				screen_input[11][8] = 2;
				screen_input[11][12] = 2;
				screen_input[12][2] = 2;
				screen_input[12][5] = 2;
				screen_input[12][8] = 2;
				screen_input[12][9] = 2;
				screen_input[12][10] = 2;
				screen_input[12][11] = 2;
				screen_input[12][12] = 2;
				screen_input[13][2] = 2;
				screen_input[13][5] = 2;
				screen_input[13][8] = 2;
				screen_input[13][12] = 2;
				screen_input[14][2] = 2;
				screen_input[14][5] = 2;
				screen_input[14][10] = 3;
				screen_input[14][12] = 2;
				screen_input[15][2] = 2;
				screen_input[15][3] = 3;
				screen_input[15][5] = 2;
				screen_input[15][8] = 2;
				screen_input[15][12] = 2;
				screen_input[16][2] = 2;
				screen_input[16][3] = 2;
				screen_input[16][4] = 2;
				screen_input[16][5] = 2;
				screen_input[16][6] = 2;
				screen_input[16][7] = 2;
				screen_input[16][8] = 2;
				screen_input[16][9] = 2;
				screen_input[16][10] = 2;
				screen_input[16][11] = 2;
				screen_input[16][12] = 2;
				battery_count = 3;
				break;
				
			case 1:
				screen_input[2][5] = 2;
				screen_input[2][6] = 2;
				screen_input[2][7] = 2;
				screen_input[2][8] = 2;
				screen_input[2][9] = 2;
				screen_input[3][5] = 2;
				screen_input[3][9] = 2;
				screen_input[4][5] = 2;
				screen_input[4][7] = 1;
				player_x = 4;
				player_y = 7;
				screen_input[4][9] = 2;
				screen_input[5][1] = 2;
				screen_input[5][2] = 2;
				screen_input[5][3] = 2;
				screen_input[5][4] = 2;
				screen_input[5][5] = 2;
				screen_input[5][9] = 2;
				screen_input[5][10] = 2;
				screen_input[5][11] = 2;
				screen_input[5][12] = 2;
				screen_input[5][13] = 2;
				screen_input[6][1] = 2;
				screen_input[6][4] = 3;
				screen_input[6][5] = 10;
				screen_input[6][13] = 2;
				screen_input[7][1] = 2;
				screen_input[7][5] = 10;
				screen_input[7][13] = 2;
				screen_input[8][1] = 2;
				screen_input[8][4] = 2;
				screen_input[8][5] = 2;
				screen_input[8][6] = 2;
				screen_input[8][7] = 2;
				screen_input[8][8] = 2;
				screen_input[8][9] = 2;
				screen_input[8][10] = 2;
				screen_input[8][13] = 2;
				screen_input[9][1] = 2;
				screen_input[9][2] = 3;
				screen_input[9][4] = 11;
				screen_input[9][7] = 3;
				screen_input[9][10] = 11;
				screen_input[9][13] = 2;
				screen_input[10][1] = 2;
				screen_input[10][4] = 2;
				screen_input[10][5] = 2;
				screen_input[10][6] = 2;
				screen_input[10][7] = 9;
				screen_input[10][8] = 2;
				screen_input[10][9] = 2;
				screen_input[10][10] = 2;
				screen_input[10][13] = 2;
				screen_input[11][1] = 2;
				screen_input[11][4] = 11;
				screen_input[11][13] = 2;
				screen_input[12][1] = 2;
				screen_input[12][4] = 11;
				screen_input[12][5] = 3;
				screen_input[12][13] = 2;
				screen_input[13][1] = 2;
				screen_input[13][2] = 2;
				screen_input[13][3] = 2;
				screen_input[13][4] = 2;
				screen_input[13][5] = 2;
				screen_input[13][6] = 2;
				screen_input[13][7] = 2;
				screen_input[13][8] = 2;
				screen_input[13][9] = 2;
				screen_input[13][10] = 2;
				screen_input[13][11] = 2;
				screen_input[13][12] = 2;
				screen_input[13][13] = 2;
				battery_count = 4;
				break;
				
			case 2:
				screen_input[3][5] = 2;
				screen_input[3][6] = 2;
				screen_input[3][7] = 2;
				screen_input[3][8] = 2;
				screen_input[3][9] = 2;
				screen_input[4][5] = 2;
				screen_input[4][9] = 2;
				screen_input[5][5] = 2;
				screen_input[5][7] = 3;
				screen_input[5][9] = 2;
				screen_input[6][5] = 2;
				screen_input[6][9] = 2;
				screen_input[7][5] = 2;
				screen_input[7][6] = 11;
				screen_input[7][7] = 8;
				screen_input[7][8] = 8;
				screen_input[7][9] = 2;
				screen_input[8][5] = 2;
				screen_input[8][6] = 8;
				screen_input[8][7] = 8;
				screen_input[8][8] = 9;
				screen_input[8][9] = 2;
				screen_input[9][5] = 2;
				screen_input[9][6] = 10;
				screen_input[9][7] = 8;
				screen_input[9][8] = 8;
				screen_input[9][9] = 2;
				screen_input[10][5] = 2;
				screen_input[10][6] = 8;
				screen_input[10][7] = 9;
				screen_input[10][8] = 8;
				screen_input[10][9] = 2;
				screen_input[11][5] = 2;
				screen_input[11][6] = 8;
				screen_input[11][7] = 8;
				screen_input[11][8] = 11;
				screen_input[11][9] = 2;
				screen_input[12][5] = 2;
				screen_input[12][6] = 11;
				screen_input[12][7] = 8;
				screen_input[12][8] = 8;
				screen_input[12][9] = 2;
				screen_input[13][5] = 2;
				screen_input[13][9] = 2;
				screen_input[14][5] = 2;
				screen_input[14][7] = 1;
				player_x = 14;
				player_y = 7;
				screen_input[14][9] = 2;
				screen_input[15][5] = 2;
				screen_input[15][9] = 2;
				screen_input[16][5] = 2;
				screen_input[16][6] = 2;
				screen_input[16][7] = 2;
				screen_input[16][8] = 2;
				screen_input[16][9] = 2;
				battery_count = 1;
				break;
				
			case 3:
				screen_input[3][0] = 2;
				screen_input[3][1] = 2;
				screen_input[3][2] = 2;
				screen_input[3][3] = 2;
				screen_input[3][4] = 2;
				screen_input[3][5] = 2;
				screen_input[3][6] = 2;
				screen_input[3][7] = 2;
				screen_input[3][8] = 2;
				screen_input[3][9] = 2;
				screen_input[3][10] = 2;
				screen_input[3][11] = 2;
				screen_input[3][12] = 2;
				screen_input[3][13] = 2;
				screen_input[3][14] = 2;
				screen_input[4][0] = 2;
				screen_input[4][5] = 11;
				screen_input[4][9] = 11;
				screen_input[4][14] = 2;
				screen_input[5][0] = 2;
				screen_input[5][5] = 2;
				screen_input[5][6] = 8;
				screen_input[5][7] = 8;
				screen_input[5][8] = 8;
				screen_input[5][9] = 2;
				screen_input[5][14] = 2;
				screen_input[6][0] = 2;
				screen_input[6][3] = 3;
				screen_input[6][5] = 2;
				screen_input[6][9] = 2;
				screen_input[6][11] = 3;
				screen_input[6][14] = 2;
				screen_input[7][0] = 2;
				screen_input[7][5] = 2;
				screen_input[7][9] = 2;
				screen_input[7][14] = 2;
				screen_input[8][0] = 2;
				screen_input[8][1] = 8;
				screen_input[8][2] = 2;
				screen_input[8][3] = 2;
				screen_input[8][4] = 2;
				screen_input[8][5] = 2;
				screen_input[8][9] = 2;
				screen_input[8][10] = 2;
				screen_input[8][11] = 2;
				screen_input[8][12] = 2;
				screen_input[8][13] = 9;
				screen_input[8][14] = 2;
				screen_input[9][0] = 2;
				screen_input[9][2] = 8;
				screen_input[9][12] = 11;
				screen_input[9][14] = 2;
				screen_input[10][0] = 2;
				screen_input[10][2] = 8;
				screen_input[10][7] = 1;
				player_x = 10;
				player_y = 7;
				screen_input[10][12] = 11;
				screen_input[10][14] = 2;
				screen_input[11][0] = 2;
				screen_input[11][2] = 8;
				screen_input[11][12] = 11;
				screen_input[11][14] = 2;
				screen_input[12][0] = 2;
				screen_input[12][1] = 8;
				screen_input[12][2] = 2;
				screen_input[12][3] = 2;
				screen_input[12][4] = 2;
				screen_input[12][5] = 2;
				screen_input[12][9] = 2;
				screen_input[12][10] = 2;
				screen_input[12][11] = 2;
				screen_input[12][12] = 2;
				screen_input[12][13] = 9;
				screen_input[12][14] = 2;
				screen_input[13][0] = 2;
				screen_input[13][5] = 2;
				screen_input[13][9] = 2;
				screen_input[13][14] = 2;
				screen_input[14][0] = 2;
				screen_input[14][3] = 3;
				screen_input[14][5] = 2;
				screen_input[14][9] = 2;
				screen_input[14][11] = 3;
				screen_input[14][14] = 2;
				screen_input[15][0] = 2;
				screen_input[15][5] = 2;
				screen_input[15][6] = 9;
				screen_input[15][7] = 9;
				screen_input[15][8] = 9;
				screen_input[15][9] = 2;
				screen_input[15][14] = 2;
				screen_input[16][0] = 2;
				screen_input[16][5] = 10;
				screen_input[16][9] = 10;
				screen_input[16][14] = 2;
				screen_input[17][0] = 2;
				screen_input[17][1] = 2;
				screen_input[17][2] = 2;
				screen_input[17][3] = 2;
				screen_input[17][4] = 2;
				screen_input[17][5] = 2;
				screen_input[17][6] = 2;
				screen_input[17][7] = 2;
				screen_input[17][8] = 2;
				screen_input[17][9] = 2;
				screen_input[17][10] = 2;
				screen_input[17][11] = 2;
				screen_input[17][12] = 2;
				screen_input[17][13] = 2;
				screen_input[17][14] = 2;
				battery_count = 4;
				break;
				
			case 4:
				screen_input[1][1] = 2;
				screen_input[1][2] = 2;
				screen_input[1][3] = 2;
				screen_input[1][4] = 2;
				screen_input[1][5] = 2;
				screen_input[1][6] = 2;
				screen_input[1][7] = 2;
				screen_input[1][8] = 2;
				screen_input[1][9] = 2;
				screen_input[1][10] = 2;
				screen_input[1][11] = 2;
				screen_input[1][12] = 2;
				screen_input[1][13] = 2;
				screen_input[2][1] = 2;
				screen_input[2][2] = 1;
				player_x = 2;
				player_y = 2;
				screen_input[2][3] = 2;
				screen_input[2][4] = 3;
				screen_input[2][5] = 2;
				screen_input[2][7] = 2;
				screen_input[2][13] = 2;
				screen_input[3][1] = 2;
				screen_input[3][3] = 2;
				screen_input[3][7] = 2;
				screen_input[3][9] = 2;
				screen_input[3][10] = 2;
				screen_input[3][11] = 2;
				screen_input[3][13] = 2;
				screen_input[4][1] = 2;
				screen_input[4][5] = 2;
				screen_input[4][7] = 2;
				screen_input[4][9] = 2;
				screen_input[4][10] = 3;
				screen_input[4][11] = 2;
				screen_input[4][13] = 2;
				screen_input[5][1] = 2;
				screen_input[5][2] = 2;
				screen_input[5][3] = 2;
				screen_input[5][4] = 9;
				screen_input[5][5] = 2;
				screen_input[5][9] = 2;
				screen_input[5][11] = 2;
				screen_input[5][13] = 2;
				screen_input[6][1] = 2;
				screen_input[6][5] = 2;
				screen_input[6][6] = 2;
				screen_input[6][7] = 2;
				screen_input[6][9] = 2;
				screen_input[6][13] = 2;
				screen_input[7][1] = 2;
				screen_input[7][3] = 2;
				screen_input[7][4] = 3;
				screen_input[7][9] = 2;
				screen_input[7][10] = 9;
				screen_input[7][11] = 2;
				screen_input[7][12] = 2;
				screen_input[7][13] = 2;
				screen_input[8][1] = 2;
				screen_input[8][3] = 2;
				screen_input[8][4] = 2;
				screen_input[8][5] = 2;
				screen_input[8][6] = 2;
				screen_input[8][7] = 2;
				screen_input[8][8] = 2;
				screen_input[8][9] = 2;
				screen_input[8][12] = 3;
				screen_input[8][13] = 2;
				screen_input[9][1] = 2;
				screen_input[9][11] = 2;
				screen_input[9][12] = 2;
				screen_input[9][13] = 2;
				screen_input[10][1] = 2;
				screen_input[10][2] = 9;
				screen_input[10][3] = 2;
				screen_input[10][4] = 2;
				screen_input[10][5] = 2;
				screen_input[10][6] = 2;
				screen_input[10][7] = 8;
				screen_input[10][8] = 2;
				screen_input[10][9] = 2;
				screen_input[10][13] = 2;
				screen_input[11][1] = 2;
				screen_input[11][6] = 2;
				screen_input[11][8] = 3;
				screen_input[11][9] = 2;
				screen_input[11][10] = 2;
				screen_input[11][11] = 2;
				screen_input[11][13] = 2;
				screen_input[12][1] = 2;
				screen_input[12][3] = 2;
				screen_input[12][4] = 2;
				screen_input[12][6] = 2;
				screen_input[12][7] = 2;
				screen_input[12][11] = 2;
				screen_input[12][13] = 2;
				screen_input[13][1] = 2;
				screen_input[13][5] = 11;
				screen_input[13][7] = 2;
				screen_input[13][8] = 2;
				screen_input[13][9] = 2;
				screen_input[13][11] = 2;
				screen_input[13][13] = 2;
				screen_input[14][1] = 2;
				screen_input[14][3] = 2;
				screen_input[14][4] = 2;
				screen_input[14][5] = 2;
				screen_input[14][8] = 3;
				screen_input[14][9] = 2;
				screen_input[14][10] = 8;
				screen_input[14][11] = 2;
				screen_input[14][12] = 8;
				screen_input[14][13] = 2;
				screen_input[15][1] = 2;
				screen_input[15][3] = 2;
				screen_input[15][4] = 3;
				screen_input[15][5] = 2;
				screen_input[15][6] = 2;
				screen_input[15][7] = 2;
				screen_input[15][8] = 2;
				screen_input[15][9] = 2;
				screen_input[15][13] = 2;
				screen_input[16][1] = 2;
				screen_input[16][3] = 2;
				screen_input[16][5] = 2;
				screen_input[16][11] = 2;
				screen_input[16][13] = 2;
				screen_input[17][1] = 2;
				screen_input[17][7] = 2;
				screen_input[17][8] = 2;
				screen_input[17][9] = 2;
				screen_input[17][12] = 3;
				screen_input[17][13] = 2;
				screen_input[18][1] = 2;
				screen_input[18][2] = 2;
				screen_input[18][3] = 2;
				screen_input[18][4] = 2;
				screen_input[18][5] = 2;
				screen_input[18][6] = 2;
				screen_input[18][7] = 2;
				screen_input[18][8] = 2;
				screen_input[18][9] = 2;
				screen_input[18][10] = 2;
				screen_input[18][11] = 2;
				screen_input[18][12] = 2;
				screen_input[18][13] = 2;
				battery_count = 8;
				break;
				
			case 5:
				screen_input[6][2] = 2;
				screen_input[6][3] = 2;
				screen_input[6][4] = 2;
				screen_input[6][5] = 2;
				screen_input[6][6] = 2;
				screen_input[6][7] = 2;
				screen_input[6][8] = 2;
				screen_input[6][9] = 2;
				screen_input[6][10] = 2;
				screen_input[6][11] = 2;
				screen_input[7][2] = 2;
				screen_input[7][6] = 2;
				screen_input[7][11] = 2;
				screen_input[8][2] = 2;
				screen_input[8][4] = 3;
				screen_input[8][6] = 4;
				screen_input[8][11] = 2;
				screen_input[9][2] = 2;
				screen_input[9][6] = 2;
				screen_input[9][11] = 2;
				screen_input[10][2] = 2;
				screen_input[10][3] = 2;
				screen_input[10][4] = 2;
				screen_input[10][5] = 2;
				screen_input[10][6] = 2;
				screen_input[10][9] = 1;
				player_x = 10;
				player_y = 9;
				screen_input[10][11] = 2;
				screen_input[11][2] = 2;
				screen_input[11][6] = 2;
				screen_input[11][11] = 2;
				screen_input[12][2] = 2;
				screen_input[12][4] = 5;
				screen_input[12][11] = 2;
				screen_input[13][2] = 2;
				screen_input[13][6] = 2;
				screen_input[13][11] = 2;
				screen_input[14][2] = 2;
				screen_input[14][3] = 2;
				screen_input[14][4] = 2;
				screen_input[14][5] = 2;
				screen_input[14][6] = 2;
				screen_input[14][7] = 2;
				screen_input[14][8] = 2;
				screen_input[14][9] = 2;
				screen_input[14][10] = 2;
				screen_input[14][11] = 2;
				battery_count = 1;
				break;
				
			case 6:
				screen_input[7][1] = 2;
				screen_input[7][2] = 2;
				screen_input[7][3] = 2;
				screen_input[7][4] = 2;
				screen_input[7][5] = 2;
				screen_input[7][6] = 2;
				screen_input[7][7] = 2;
				screen_input[7][8] = 2;
				screen_input[7][9] = 2;
				screen_input[7][10] = 2;
				screen_input[7][11] = 2;
				screen_input[7][12] = 2;
				screen_input[8][1] = 2;
				screen_input[8][2] = 7;
				screen_input[8][6] = 7;
				screen_input[8][9] = 7;
				screen_input[8][12] = 2;
				screen_input[9][1] = 2;
				screen_input[9][2] = 7;
				screen_input[9][4] = 7;
				screen_input[9][7] = 7;
				screen_input[9][12] = 2;
				screen_input[10][1] = 2;
				screen_input[10][2] = 7;
				screen_input[10][5] = 7;
				screen_input[10][8] = 7;
				screen_input[10][10] = 1;
				player_x = 10;
				player_y = 10;
				screen_input[10][12] = 2;
				screen_input[11][1] = 2;
				screen_input[11][2] = 3;
				screen_input[11][3] = 7;
				screen_input[11][6] = 7;
				screen_input[11][12] = 2;
				screen_input[12][1] = 2;
				screen_input[12][7] = 7;
				screen_input[12][9] = 7;
				screen_input[12][12] = 2;
				screen_input[13][1] = 2;
				screen_input[13][2] = 2;
				screen_input[13][3] = 2;
				screen_input[13][4] = 2;
				screen_input[13][5] = 2;
				screen_input[13][6] = 2;
				screen_input[13][7] = 2;
				screen_input[13][8] = 2;
				screen_input[13][9] = 2;
				screen_input[13][10] = 2;
				screen_input[13][11] = 2;
				screen_input[13][12] = 2;
				battery_count = 1;
				break;
				
			case 7:
				screen_input[2][2] = 2;
				screen_input[2][3] = 2;
				screen_input[2][4] = 2;
				screen_input[2][5] = 2;
				screen_input[2][6] = 2;
				screen_input[2][7] = 2;
				screen_input[2][8] = 2;
				screen_input[2][9] = 2;
				screen_input[2][10] = 2;
				screen_input[2][11] = 2;
				screen_input[2][12] = 2;
				screen_input[3][2] = 2;
				screen_input[3][7] = 1;
				player_x = 3;
				player_y = 7;
				screen_input[3][11] = 5;
				screen_input[3][12] = 2;
				screen_input[4][2] = 2;
				screen_input[4][11] = 5;
				screen_input[4][12] = 2;
				screen_input[5][2] = 2;
				screen_input[5][3] = 2;
				screen_input[5][4] = 2;
				screen_input[5][5] = 2;
				screen_input[5][6] = 2;
				screen_input[5][8] = 2;
				screen_input[5][9] = 2;
				screen_input[5][10] = 2;
				screen_input[5][11] = 2;
				screen_input[5][12] = 2;
				screen_input[6][2] = 2;
				screen_input[6][6] = 4;
				screen_input[6][8] = 4;
				screen_input[6][12] = 2;
				screen_input[7][2] = 2;
				screen_input[7][4] = 5;
				screen_input[7][6] = 2;
				screen_input[7][8] = 2;
				screen_input[7][10] = 5;
				screen_input[7][12] = 2;
				screen_input[8][2] = 2;
				screen_input[8][6] = 2;
				screen_input[8][8] = 2;
				screen_input[8][12] = 2;
				screen_input[9][2] = 2;
				screen_input[9][3] = 2;
				screen_input[9][4] = 2;
				screen_input[9][5] = 2;
				screen_input[9][6] = 2;
				screen_input[9][8] = 2;
				screen_input[9][9] = 2;
				screen_input[9][11] = 2;
				screen_input[9][12] = 2;
				screen_input[10][2] = 2;
				screen_input[10][6] = 2;
				screen_input[10][8] = 2;
				screen_input[10][12] = 2;
				screen_input[11][2] = 2;
				screen_input[11][4] = 3;
				screen_input[11][6] = 4;
				screen_input[11][8] = 4;
				screen_input[11][10] = 5;
				screen_input[11][12] = 2;
				screen_input[12][2] = 2;
				screen_input[12][6] = 2;
				screen_input[12][8] = 2;
				screen_input[12][12] = 2;
				screen_input[13][2] = 2;
				screen_input[13][3] = 2;
				screen_input[13][4] = 2;
				screen_input[13][5] = 2;
				screen_input[13][6] = 2;
				screen_input[13][8] = 2;
				screen_input[13][9] = 2;
				screen_input[13][10] = 2;
				screen_input[13][11] = 2;
				screen_input[13][12] = 2;
				screen_input[14][2] = 2;
				screen_input[14][6] = 2;
				screen_input[14][8] = 2;
				screen_input[14][12] = 2;
				screen_input[15][2] = 2;
				screen_input[15][4] = 5;
				screen_input[15][6] = 2;
				screen_input[15][8] = 2;
				screen_input[15][10] = 3;
				screen_input[15][12] = 2;
				screen_input[16][2] = 2;
				screen_input[16][6] = 4;
				screen_input[16][8] = 4;
				screen_input[16][12] = 2;
				screen_input[17][2] = 2;
				screen_input[17][3] = 2;
				screen_input[17][4] = 2;
				screen_input[17][5] = 2;
				screen_input[17][6] = 2;
				screen_input[17][7] = 7;
				screen_input[17][8] = 2;
				screen_input[17][9] = 2;
				screen_input[17][10] = 2;
				screen_input[17][11] = 2;
				screen_input[17][12] = 2;
				screen_input[18][6] = 2;
				screen_input[18][7] = 2;
				screen_input[18][8] = 2;
				battery_count = 2;
				break;
				
			case 8:
				screen_input[2][1] = 2;
				screen_input[2][2] = 2;
				screen_input[2][3] = 2;
				screen_input[2][4] = 2;
				screen_input[2][5] = 2;
				screen_input[3][1] = 2;
				screen_input[3][5] = 2;
				screen_input[4][1] = 2;
				screen_input[4][3] = 1;
				player_x = 4;
				player_y = 3;
				screen_input[4][5] = 2;
				screen_input[5][1] = 2;
				screen_input[5][5] = 2;
				screen_input[6][1] = 2;
				screen_input[6][5] = 2;
				screen_input[7][1] = 2;
				screen_input[7][5] = 2;
				screen_input[8][1] = 2;
				screen_input[8][5] = 2;
				screen_input[8][6] = 2;
				screen_input[8][7] = 2;
				screen_input[8][8] = 2;
				screen_input[8][9] = 2;
				screen_input[8][10] = 2;
				screen_input[8][11] = 2;
				screen_input[8][12] = 2;
				screen_input[9][1] = 2;
				screen_input[9][8] = 7;
				screen_input[9][10] = 6;
				screen_input[9][12] = 2;
				screen_input[10][1] = 2;
				screen_input[10][3] = 6;
				screen_input[10][8] = 7;
				screen_input[10][10] = 3;
				screen_input[10][12] = 2;
				screen_input[11][1] = 2;
				screen_input[11][8] = 7;
				screen_input[11][10] = 6;
				screen_input[11][12] = 2;
				screen_input[12][1] = 2;
				screen_input[12][2] = 2;
				screen_input[12][3] = 2;
				screen_input[12][4] = 2;
				screen_input[12][5] = 7;
				screen_input[12][6] = 7;
				screen_input[12][7] = 7;
				screen_input[12][8] = 2;
				screen_input[12][9] = 2;
				screen_input[12][10] = 2;
				screen_input[12][11] = 2;
				screen_input[12][12] = 2;
				screen_input[13][4] = 2;
				screen_input[13][5] = 7;
				screen_input[13][6] = 7;
				screen_input[13][7] = 7;
				screen_input[13][8] = 2;
				screen_input[14][4] = 2;
				screen_input[14][8] = 2;
				screen_input[15][4] = 2;
				screen_input[15][6] = 3;
				screen_input[15][8] = 2;
				screen_input[16][4] = 2;
				screen_input[16][5] = 2;
				screen_input[16][6] = 2;
				screen_input[16][7] = 2;
				screen_input[16][8] = 2;
				battery_count = 2;
				break;
				
			case 9:
				screen_input[6][2] = 2;
				screen_input[6][3] = 2;
				screen_input[6][4] = 2;
				screen_input[6][5] = 2;
				screen_input[6][6] = 2;
				screen_input[6][7] = 2;
				screen_input[6][8] = 2;
				screen_input[6][9] = 2;
				screen_input[6][10] = 2;
				screen_input[7][2] = 2;
				screen_input[7][10] = 2;
				screen_input[8][2] = 2;
				screen_input[8][4] = 6;
				screen_input[8][6] = 2;
				screen_input[8][8] = 1;
				player_x = 8;
				player_y = 8;
				screen_input[8][10] = 2;
				screen_input[9][2] = 2;
				screen_input[9][10] = 2;
				screen_input[10][2] = 2;
				screen_input[10][3] = 2;
				screen_input[10][4] = 4;
				screen_input[10][5] = 2;
				screen_input[10][6] = 2;
				screen_input[10][10] = 2;
				screen_input[11][2] = 2;
				screen_input[11][4] = 7;
				screen_input[11][6] = 2;
				screen_input[11][10] = 2;
				screen_input[12][2] = 2;
				screen_input[12][4] = 3;
				screen_input[12][6] = 2;
				screen_input[12][8] = 5;
				screen_input[12][10] = 2;
				screen_input[13][2] = 2;
				screen_input[13][6] = 2;
				screen_input[13][10] = 2;
				screen_input[14][2] = 2;
				screen_input[14][3] = 2;
				screen_input[14][4] = 2;
				screen_input[14][5] = 2;
				screen_input[14][6] = 2;
				screen_input[14][7] = 2;
				screen_input[14][8] = 2;
				screen_input[14][9] = 2;
				screen_input[14][10] = 2;
				battery_count = 1;
				break;
				
			case 10:
				screen_input[1][5] = 2;
				screen_input[1][6] = 2;
				screen_input[1][7] = 2;
				screen_input[1][8] = 2;
				screen_input[1][9] = 2;
				screen_input[2][5] = 2;
				screen_input[2][9] = 2;
				screen_input[3][5] = 2;
				screen_input[3][7] = 1;
				player_x = 3;
				player_y = 7;
				screen_input[3][9] = 2;
				screen_input[4][5] = 2;
				screen_input[4][9] = 2;
				screen_input[5][2] = 2;
				screen_input[5][3] = 2;
				screen_input[5][4] = 2;
				screen_input[5][5] = 2;
				screen_input[5][9] = 2;
				screen_input[5][10] = 2;
				screen_input[5][11] = 2;
				screen_input[5][12] = 2;
				screen_input[6][2] = 2;
				screen_input[6][3] = 5;
				screen_input[6][5] = 7;
				screen_input[6][9] = 4;
				screen_input[6][11] = 6;
				screen_input[6][12] = 2;
				screen_input[7][2] = 2;
				screen_input[7][3] = 2;
				screen_input[7][4] = 2;
				screen_input[7][5] = 2;
				screen_input[7][9] = 2;
				screen_input[7][10] = 2;
				screen_input[7][11] = 2;
				screen_input[7][12] = 2;
				screen_input[8][5] = 2;
				screen_input[8][6] = 6;
				screen_input[8][8] = 5;
				screen_input[8][9] = 2;
				screen_input[9][1] = 2;
				screen_input[9][2] = 2;
				screen_input[9][3] = 2;
				screen_input[9][4] = 2;
				screen_input[9][5] = 2;
				screen_input[9][9] = 2;
				screen_input[9][10] = 2;
				screen_input[9][11] = 2;
				screen_input[9][12] = 2;
				screen_input[9][13] = 2;
				screen_input[10][1] = 2;
				screen_input[10][5] = 2;
				screen_input[10][9] = 2;
				screen_input[10][13] = 2;
				screen_input[11][1] = 2;
				screen_input[11][2] = 6;
				screen_input[11][3] = 5;
				screen_input[11][5] = 4;
				screen_input[11][9] = 4;
				screen_input[11][11] = 5;
				screen_input[11][12] = 6;
				screen_input[11][13] = 2;
				screen_input[12][1] = 2;
				screen_input[12][5] = 2;
				screen_input[12][6] = 7;
				screen_input[12][7] = 7;
				screen_input[12][8] = 7;
				screen_input[12][9] = 2;
				screen_input[12][13] = 2;
				screen_input[13][1] = 2;
				screen_input[13][2] = 2;
				screen_input[13][3] = 2;
				screen_input[13][4] = 2;
				screen_input[13][5] = 2;
				screen_input[13][6] = 7;
				screen_input[13][7] = 7;
				screen_input[13][8] = 7;
				screen_input[13][9] = 2;
				screen_input[13][10] = 2;
				screen_input[13][11] = 2;
				screen_input[13][12] = 2;
				screen_input[13][13] = 2;
				screen_input[14][5] = 2;
				screen_input[14][6] = 2;
				screen_input[14][7] = 4;
				screen_input[14][8] = 2;
				screen_input[14][9] = 2;
				screen_input[15][5] = 2;
				screen_input[15][7] = 7;
				screen_input[15][9] = 2;
				screen_input[16][5] = 2;
				screen_input[16][9] = 2;
				screen_input[17][5] = 2;
				screen_input[17][7] = 3;
				screen_input[17][9] = 2;
				screen_input[18][5] = 2;
				screen_input[18][6] = 2;
				screen_input[18][7] = 2;
				screen_input[18][8] = 2;
				screen_input[18][9] = 2;
				battery_count = 1;
				break;
				
			case 11:
				screen_input[1][1] = 2;
				screen_input[1][2] = 2;
				screen_input[1][3] = 2;
				screen_input[1][4] = 2;
				screen_input[1][5] = 2;
				screen_input[1][6] = 2;
				screen_input[1][7] = 2;
				screen_input[1][8] = 2;
				screen_input[1][9] = 2;
				screen_input[1][10] = 2;
				screen_input[1][11] = 2;
				screen_input[1][12] = 2;
				screen_input[1][13] = 2;
				screen_input[2][1] = 2;
				screen_input[2][5] = 2;
				screen_input[2][9] = 2;
				screen_input[2][13] = 2;
				screen_input[3][1] = 2;
				screen_input[3][2] = 5;
				screen_input[3][4] = 6;
				screen_input[3][5] = 2;
				screen_input[3][7] = 6;
				screen_input[3][9] = 4;
				screen_input[3][11] = 1;
				player_x = 3;
				player_y = 11;
				screen_input[3][13] = 2;
				screen_input[4][1] = 2;
				screen_input[4][5] = 2;
				screen_input[4][9] = 2;
				screen_input[4][13] = 2;
				screen_input[5][1] = 2;
				screen_input[5][2] = 7;
				screen_input[5][3] = 7;
				screen_input[5][4] = 7;
				screen_input[5][5] = 2;
				screen_input[5][6] = 2;
				screen_input[5][7] = 2;
				screen_input[5][8] = 2;
				screen_input[5][9] = 2;
				screen_input[5][13] = 2;
				screen_input[6][1] = 2;
				screen_input[6][13] = 2;
				screen_input[7][1] = 2;
				screen_input[7][13] = 2;
				screen_input[8][1] = 2;
				screen_input[8][13] = 2;
				screen_input[9][1] = 2;
				screen_input[9][13] = 2;
				screen_input[10][1] = 2;
				screen_input[10][2] = 8;
				screen_input[10][3] = 8;
				screen_input[10][4] = 8;
				screen_input[10][5] = 2;
				screen_input[10][6] = 2;
				screen_input[10][7] = 9;
				screen_input[10][8] = 2;
				screen_input[10][9] = 2;
				screen_input[10][10] = 2;
				screen_input[10][11] = 8;
				screen_input[10][12] = 2;
				screen_input[10][13] = 2;
				screen_input[11][1] = 2;
				screen_input[11][5] = 2;
				screen_input[11][9] = 11;
				screen_input[11][13] = 2;
				screen_input[12][1] = 2;
				screen_input[12][5] = 2;
				screen_input[12][9] = 11;
				screen_input[12][13] = 2;
				screen_input[13][1] = 2;
				screen_input[13][2] = 7;
				screen_input[13][3] = 7;
				screen_input[13][4] = 7;
				screen_input[13][5] = 2;
				screen_input[13][9] = 11;
				screen_input[13][13] = 2;
				screen_input[14][1] = 2;
				screen_input[14][2] = 2;
				screen_input[14][3] = 4;
				screen_input[14][4] = 2;
				screen_input[14][5] = 2;
				screen_input[14][6] = 8;
				screen_input[14][7] = 8;
				screen_input[14][8] = 8;
				screen_input[14][9] = 2;
				screen_input[14][10] = 9;
				screen_input[14][11] = 9;
				screen_input[14][12] = 11;
				screen_input[14][13] = 2;
				screen_input[15][1] = 2;
				screen_input[15][5] = 2;
				screen_input[15][9] = 10;
				screen_input[15][13] = 2;
				screen_input[16][1] = 2;
				screen_input[16][3] = 3;
				screen_input[16][5] = 2;
				screen_input[16][7] = 5;
				screen_input[16][9] = 10;
				screen_input[16][13] = 2;
				screen_input[17][1] = 2;
				screen_input[17][5] = 2;
				screen_input[17][9] = 9;
				screen_input[17][13] = 2;
				screen_input[18][1] = 2;
				screen_input[18][2] = 2;
				screen_input[18][3] = 2;
				screen_input[18][4] = 2;
				screen_input[18][5] = 2;
				screen_input[18][6] = 2;
				screen_input[18][7] = 2;
				screen_input[18][8] = 2;
				screen_input[18][9] = 2;
				screen_input[18][10] = 2;
				screen_input[18][11] = 2;
				screen_input[18][12] = 2;
				screen_input[18][13] = 2;
				battery_count = 1;
				break;
		}
	}
	
	//Draw ALL the things
	private void render(Image[] sprites) {
		BufferStrategy bs = this.getBufferStrategy();
		if(bs == null) {
			this.createBufferStrategy(3);
			return;
		}
		
		Graphics g = bs.getDrawGraphics();
		
		g.setColor(Color.black);
		g.fillRect(0, 0, WIDTH, HEIGHT);
		
		for (int i = 0; i < 20 ; i++) {
			for (int j = 0; j < 15; j++) {
				g.drawImage(sprites[0], i*32, j*32, null);
				
				if (screen_input[i][j] > 0 && screen_input[i][j] < 13) {
					g.drawImage(sprites[screen_input[i][j]], i*32, j*32, null);
				}	
				
				if (screen_input[i][j] == 13) {
					g.drawImage(sprites[8], i*32, j*32, null);
					g.drawImage(sprites[1], i*32, j*32, null);
				}
				
				if (screen_input[i][j] == 14) {
					g.drawImage(sprites[9], i*32, j*32, null);
					g.drawImage(sprites[1], i*32, j*32, null);
				}
				
				if (screen_input[i][j] == 15) {
					g.drawImage(sprites[10], i*32, j*32, null);
					g.drawImage(sprites[1], i*32, j*32, null);
				}
				
				if (screen_input[i][j] == 16) {
					g.drawImage(sprites[11], i*32, j*32, null);
					g.drawImage(sprites[1], i*32, j*32, null);
				}
				
				if (screen_input[i][j] == 17) {
					g.drawImage(sprites[12], i*32, j*32, null);
					g.drawImage(sprites[1], i*32, j*32, null);
				}
			}
		}
		
		g.dispose();
		bs.show();
	}
}

